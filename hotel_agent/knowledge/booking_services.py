
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from .models import IndianHotel, RoomInventory, Reservation


def seed_demo_inventory(days=30):
    """
    Create clearly labelled demo inventory for selected hotels.
    This is simulated inventory, not live PMS data.
    """
    today = date.today()

    hotels = IndianHotel.objects.filter(
        city__iexact="Indore"
    ).order_by("id")[:5]

    if not hotels.exists():
        hotels = IndianHotel.objects.order_by("id")[:5]

    created = 0

    with transaction.atomic():
        for hotel in hotels:
            room_types = [
                ("Standard", Decimal("2500.00"), 5),
                ("Deluxe", Decimal("4000.00"), 3),
            ]

            for room_type, price, total_rooms in room_types:
                for offset in range(days):
                    _, was_created = RoomInventory.objects.get_or_create(
                        hotel=hotel,
                        room_type=room_type,
                        date=today + timedelta(days=offset),
                        defaults={
                            "total_rooms": total_rooms,
                            "price_per_night": price,
                        },
                    )
                    if was_created:
                        created += 1

    return {
        "hotels_seeded": hotels.count(),
        "inventory_rows_created": created,
        "inventory_type": "SIMULATED_DEMO",
    }


def check_room_availability(
    hotel_id,
    room_type,
    check_in,
    check_out,
    rooms=1,
):
    """
    Check every night in [check_in, check_out).
    Checkout day is not charged as an occupied night.
    """
    if check_in < date.today():
        raise ValueError("Check-in cannot be in the past.")

    if check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")

    if rooms < 1:
        raise ValueError("At least one room must be requested.")

    nights = (check_out - check_in).days
    required_dates = [
        check_in + timedelta(days=offset)
        for offset in range(nights)
    ]

    inventory = list(
        RoomInventory.objects.filter(
            hotel_id=hotel_id,
            room_type__iexact=room_type,
            date__in=required_dates,
        ).order_by("date")
    )

    inventory_by_date = {item.date: item for item in inventory}

    if len(inventory_by_date) != nights:
        return {
            "available": False,
            "reason": "Inventory is missing for one or more nights.",
        }

    nightly_prices = []
    for night in required_dates:
        item = inventory_by_date[night]

        reserved = Reservation.objects.filter(
            hotel_id=hotel_id,
            room_type__iexact=room_type,
            status="CONFIRMED",
            check_in__lt=night + timedelta(days=1),
            check_out__gt=night,
        ).aggregate(total=Sum("rooms"))["total"] or 0

        remaining = item.total_rooms - reserved

        if remaining < rooms:
            return {
                "available": False,
                "reason": f"Not enough rooms available for {night}.",
                "remaining_rooms": max(remaining, 0),
            }

        nightly_prices.append(item.price_per_night)

    # Require a consistent nightly price for this demo booking.
    if len(set(nightly_prices)) != 1:
        return {
            "available": False,
            "reason": "Nightly prices vary. Price calculation needs review.",
        }

    price_per_night = nightly_prices[0]

    return {
        "available": True,
        "nights": nights,
        "rooms": rooms,
        "price_per_night": str(price_per_night),
        "total_price": str(price_per_night * nights * rooms),
        "inventory_type": "SIMULATED_DEMO",
    }
