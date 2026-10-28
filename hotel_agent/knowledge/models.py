
from django.db import models


class HotelKnowledge(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return self.title

class HotelListing(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    location = models.CharField(max_length=255, blank=True)
    rating = models.CharField(max_length=50, blank=True)
    review_score = models.CharField(max_length=50, blank=True)
    room_type = models.CharField(max_length=255, blank=True)
    bed_type = models.CharField(max_length=255, blank=True)
    price_original = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name} - {self.room_type}"


class RoomReview(models.Model):
    property_name = models.CharField(max_length=255, db_index=True)
    price_original = models.CharField(max_length=100, blank=True)
    review_count = models.IntegerField(default=0)
    comment = models.TextField(blank=True)

    def __str__(self):
        return self.property_name


class BookingRecord(models.Model):
    hotel = models.CharField(max_length=100, db_index=True)
    is_canceled = models.BooleanField(default=False)
    arrival_year = models.IntegerField(null=True, blank=True)
    arrival_month = models.CharField(max_length=30, blank=True)
    adults = models.IntegerField(default=0)
    children = models.FloatField(default=0)
    country = models.CharField(max_length=10, blank=True)
    reserved_room_type = models.CharField(max_length=10, blank=True)
    adr = models.FloatField(default=0)
    reservation_status = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.hotel} - {self.reservation_status}"


class HotelFAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, default="general")
    language = models.CharField(max_length=20, default="en")
    source = models.CharField(max_length=100, default="demo")
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.question[:100]


class GuestIntentExample(models.Model):
    instruction = models.TextField()
    intent = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    tags = models.CharField(max_length=255, blank=True)
    response = models.TextField()

    def __str__(self):
        return f"{self.intent}: {self.instruction[:80]}"


class IndianHotel(models.Model):
    property_id = models.CharField(max_length=100, blank=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=100, blank=True, db_index=True)
    address = models.TextField(blank=True)
    locality = models.CharField(max_length=255, blank=True)
    hotel_type = models.CharField(max_length=100, blank=True)
    star_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review_rating = models.FloatField(null=True, blank=True)
    review_count = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    facilities = models.TextField(blank=True)
    room_type = models.TextField(blank=True)
    room_facilities = models.TextField(blank=True)
    checkin_checkout_policy = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.city}"


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
    )
    guest_name = models.CharField(max_length=150, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    hotel_name = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="OPEN",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            import uuid
            self.ticket_id = f"TKT-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"



import uuid
from django.db import models


class RoomInventory(models.Model):
    """Number of rooms available for a hotel and room type on a date."""

    hotel = models.ForeignKey(
        IndianHotel,
        on_delete=models.PROTECT,
        related_name="room_inventory",
    )
    room_type = models.CharField(max_length=150)
    date = models.DateField(db_index=True)
    total_rooms = models.PositiveIntegerField(default=1)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hotel", "room_type", "date"],
                name="unique_hotel_room_inventory_date",
            ),
        ]
        ordering = ["date", "hotel__name"]

    def __str__(self):
        return f"{self.hotel.name} | {self.room_type} | {self.date}"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    booking_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
    )
    hotel = models.ForeignKey(
        IndianHotel,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    room_type = models.CharField(max_length=150)
    guest_name = models.CharField(max_length=150)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    check_in = models.DateField(db_index=True)
    check_out = models.DateField(db_index=True)
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    rooms = models.PositiveSmallIntegerField(default=1)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="CONFIRMED",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"BK-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} - {self.guest_name}"


class Lead(models.Model):
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("CONTACTED", "Contacted"),
        ("QUALIFIED", "Qualified"),
        ("CONVERTED", "Converted"),
        ("LOST", "Lost"),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    preferred_city = models.CharField(max_length=100, blank=True)
    requirements = models.TextField(blank=True)
    source = models.CharField(max_length=50, default="AI_CHAT")
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="NEW",
        db_index=True,
    )
    follow_up_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.status}"
