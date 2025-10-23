from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Area


def home(request):
    menu_items = [
        {
            "img": "booking/img/menu/food1.png",
            "name": "Smoky Duck Ramen",
            "desc": "rich shoyu broth, ajitama",
            "price": "₽ 690",
        },
        {
            "img": "booking/img/menu/food2.png",
            "name": "Yuzu Chicken Ramen",
            "desc": "citrus aroma, light broth",
            "price": "₽ 650",
        },
        {
            "img": "booking/img/menu/food3.png",
            "name": "Spicy Miso Ramen",
            "desc": "tofu, corn, chili oil",
            "price": "₽ 620",
        },
        {
            "img": "booking/img/menu/food4.png",
            "name": "Matcha Cheesecake",
            "desc": "yuzu zest, sesame crust",
            "price": "₽ 390",
        },
        {
            "img": "booking/img/menu/food5.png",
            "name": "Ramen Hikari",
            "desc": "japanese ramen in black matte bowl",
            "price": "₽ 730",
        },
        {
            "img": "booking/img/menu/food6.png",
            "name": "Tempura Udon",
            "desc": "crispy shrimp, dashi broth",
            "price": "₽ 520",
        },
    ]
    return render(request, "booking/index.html", {"menu_items": menu_items})


@ensure_csrf_cookie
def booking_page(request):
    areas = Area.objects.filter(is_active=True).order_by("order", "name")
    return render(request, "booking/booking.html", {"areas": areas})
