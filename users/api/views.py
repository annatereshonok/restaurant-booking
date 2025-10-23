from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from users.models import CustomUser


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    data = request.data
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    phone = data.get("phone", "").strip()

    user = CustomUser.objects.create_user(
        email=email, password=password, first_name=first_name, last_name=last_name
    )
    user.phone = phone
    user.save()

    auth_user = authenticate(request, username=email, password=password)
    if auth_user is not None:
        login(request, auth_user)

    return Response(
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": getattr(user, "phone", ""),
            "authenticated": True,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_view(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    user = authenticate(request, email=email, password=password)
    if not user:
        return Response({"detail": "Неверные учетные данные"}, status=400)
    login(request, user)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return redirect("home")


@api_view(["GET"])
def me(request):
    if not request.user.is_authenticated:
        return Response({"is_authenticated": False})

    u = request.user
    return Response(
        {
            "is_authenticated": True,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "phone": u.phone,
            "avatar_url": u.avatar.url if getattr(u, "avatar", None) else None,
        }
    )


@api_view(["PATCH", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def me_update(request):
    u: CustomUser = request.user
    data = request.data

    for field in ["first_name", "last_name", "phone"]:
        if field in data and str(data.get(field)).strip() != "":
            setattr(u, field, str(data.get(field)).strip())

    if "avatar" in request.FILES:
        u.avatar = request.FILES["avatar"]

    try:
        u.full_clean()
        u.save()
    except Exception as e:
        return Response(
            {"detail": f"Не удалось сохранить профиль: {e}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "is_authenticated": True,
            "email": u.email,
            "first_name": u.first_name,
            "phone": u.phone,
            "favorite_dish": getattr(u, "favorite_dish", None),
            "avatar_url": u.avatar.url if u.avatar else None,
        }
    )
