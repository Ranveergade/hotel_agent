
from django.urls import path

from .views import (
    test_retrieval,
    search_hotels,
    search_indian_hotels,
    hotel_ai_assistant,
    create_support_ticket,
    staff_dashboard
)

from . import booking_views


urlpatterns = [
    # Existing hotel and AI endpoints
    path("test-retrieval/", test_retrieval),
    path("hotels/", search_hotels),
    path("indian-hotels/", search_indian_hotels),
    path("ai-assistant/", hotel_ai_assistant),
    path("support-tickets/", create_support_ticket),

    # Booking engine
    path("demo/seed-inventory/", booking_views.seed_inventory_api),
    path("booking/availability/", booking_views.check_availability_api),
    path("booking/create/", booking_views.create_reservation_api),

    # Lead capture
    path("leads/create/", booking_views.create_lead_api),

    # Staff dashboard data
    path("bookings/", booking_views.reservation_list_api),
    path("staff-dashboard/", staff_dashboard, name="staff_dashboard"),
]
