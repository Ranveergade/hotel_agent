
import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import IndianHotel, RoomInventory, Reservation, Lead
from .booking_services import seed_demo_inventory, check_room_availability


def read_json(request):
    try:
        return json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Request body must contain valid JSON.")


def parse_date(value, field):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must use YYYY-MM-DD format.")


@csrf_exempt
@require_POST
def seed_inventory_api(request):
    """Demo-only endpoint. Do not expose publicly."""
    try:
        data = read_json(request)
        result = seed_demo_inventory(days=30)
        return JsonResponse({"success": True, **result})
    except (ValueError, TypeError) as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


@csrf_exempt
@require_POST
def check_availability_api(request):
    try:
        data = read_json(request)
        hotel_id = int(data["hotel_id"])
        room_type = str(data["room_type"]).strip()
        check_in = parse_date(data.get("check_in"), "check_in")
        check_out = parse_date(data.get("check_out"), "check_out")
        rooms = int(data.get("rooms", 1))

        if not room_type:
            raise ValueError("room_type is required.")

        if not IndianHotel.objects.filter(pk=hotel_id).exists():
            return JsonResponse(
                {"success": False, "error": "Hotel not found."},
                status=404,
            )

        result = check_room_availability(
            hotel_id, room_type, check_in, check_out, rooms
        )
        return JsonResponse({"success": True, **result})

    except (KeyError, ValueError, TypeError) as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


@csrf_exempt
@require_POST
def create_reservation_api(request):
    try:
        data = read_json(request)

        hotel_id = int(data["hotel_id"])
        room_type = str(data["room_type"]).strip()
        guest_name = str(data["guest_name"]).strip()
        guest_email = str(data["guest_email"]).strip()
        guest_phone = str(data.get("guest_phone", "")).strip()
        check_in = parse_date(data.get("check_in"), "check_in")
        check_out = parse_date(data.get("check_out"), "check_out")
        adults = int(data.get("adults", 1))
        children = int(data.get("children", 0))
        rooms = int(data.get("rooms", 1))

        if not guest_name or not guest_email or not room_type:
            raise ValueError("guest_name, guest_email and room_type are required.")

        if adults < 1 or children < 0 or rooms < 1:
            raise ValueError("Adults and rooms must be at least 1; children cannot be negative.")

        hotel = IndianHotel.objects.filter(pk=hotel_id).first()
        if not hotel:
            return JsonResponse(
                {"success": False, "error": "Hotel not found."},
                status=404,
            )

        with transaction.atomic():
            # Lock the inventory rows while checking and creating the booking.
            inventory_rows = list(
                RoomInventory.objects.select_for_update().filter(
                    hotel_id=hotel_id,
                    room_type__iexact=room_type,
                    date__gte=check_in,
                    date__lt=check_out,
                ).order_by("date")
            )

            result = check_room_availability(
                hotel_id, room_type, check_in, check_out, rooms
            )

            if not result.get("available"):
                return JsonResponse(
                    {"success": False, **result},
                    status=409,
                )

            reservation = Reservation.objects.create(
                hotel=hotel,
                room_type=room_type,
                guest_name=guest_name,
                guest_email=guest_email,
                guest_phone=guest_phone,
                check_in=check_in,
                check_out=check_out,
                adults=adults,
                children=children,
                rooms=rooms,
                price_per_night=Decimal(result["price_per_night"]),
                total_price=Decimal(result["total_price"]),
            )

        return JsonResponse({
            "success": True,
            "message": "Demo reservation created successfully.",
            "booking_id": reservation.booking_id,
            "status": reservation.status,
            "hotel": hotel.name,
            "room_type": reservation.room_type,
            "check_in": str(reservation.check_in),
            "check_out": str(reservation.check_out),
            "rooms": reservation.rooms,
            "total_price": str(reservation.total_price),
            "currency": "INR",
            "inventory_type": "SIMULATED_DEMO",
        }, status=201)

    except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


@csrf_exempt
@require_POST
def create_lead_api(request):
    try:
        data = read_json(request)
        name = str(data.get("name", "")).strip()

        if not name:
            raise ValueError("Guest name is required.")

        lead = Lead.objects.create(
            name=name,
            email=str(data.get("email", "")).strip(),
            phone=str(data.get("phone", "")).strip(),
            preferred_city=str(data.get("preferred_city", "")).strip(),
            requirements=str(data.get("requirements", "")).strip(),
            source="AI_CHAT",
        )

        return JsonResponse({
            "success": True,
            "lead_id": lead.id,
            "name": lead.name,
            "status": lead.status,
            "message": "Guest enquiry saved.",
        }, status=201)

    except (ValueError, TypeError) as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


@require_GET
def reservation_list_api(request):
    reservations = Reservation.objects.select_related("hotel").order_by("-created_at")[:100]

    return JsonResponse({
        "success": True,
        "reservations": [
            {
                "booking_id": r.booking_id,
                "guest_name": r.guest_name,
                "guest_email": r.guest_email,
                "hotel": r.hotel.name,
                "city": r.hotel.city,
                "room_type": r.room_type,
                "check_in": str(r.check_in),
                "check_out": str(r.check_out),
                "total_price": str(r.total_price),
                "status": r.status,
            }
            for r in reservations
        ],
    })
