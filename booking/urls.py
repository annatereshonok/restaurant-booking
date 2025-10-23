from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from views import home, booking_page


@staff_member_required
def manager_dashboard_page(request):
    return render(request, "booking/manager_dashboard.html")


urlpatterns = [
    path("", home, name="home"),
    path("booking/", booking_page, name="booking_page"),
    path("manager/", manager_dashboard_page, name="manager_dashboard"),
]
