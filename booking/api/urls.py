from django.urls import path
from . import views

urlpatterns = [
    path("availability/", views.availability, name="api_availability"),
    path("layout/tables/", views.tables_list, name="api_tables"),
    path("layout/table-types/", views.table_types, name="api_table_types"),
    path("layout/areas/", views.AreaListAPIView.as_view(), name="api_areas"),
    # bookings
    path("bookings/", views.create_booking, name="api_create_booking"),
    path(
        "me/bookings-by-status/",
        views.my_bookings_by_status,
        name="api_my_bookings_by_status",
    ),
    path(
        "me/bookings/<int:pk>/cancel",
        views.my_booking_cancel,
        name="api_my_booking_cancel",
    ),
    # manager endpoints
    path(
        "manager/bookings/<int:pk>/confirm",
        views.manager_confirm,
        name="api_manager_confirm",
    ),
    path(
        "manager/bookings/<int:pk>/cancel",
        views.manager_cancel,
        name="api_manager_cancel",
    ),
    path(
        "manager/bookings/",
        views.manager_bookings_list,
        name="api_manager_bookings_list",
    ),
    path(
        "manager/bookings/<int:pk>/status",
        views.manager_set_status,
        name="api_manager_set_status",
    ),
    path(
        "manager/statuses/",
        views.manager_status_choices,
        name="api_manager_status_choices",
    ),
    path(
        "me/bookings/<int:pk>/ical", views.my_booking_ical, name="api_my_booking_ical"
    ),
    path("ical", views.booking_ical_by_token, name="api_booking_ical_by_token"),
]
