from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="api_auth_register"),
    path("login/", views.login_view, name="api_auth_login"),
    path("logout/", views.logout_view, name="api_auth_logout"),
    path("me/update", views.me_update, name="api_auth_me_update"),
    path("me/", views.me, name="api_auth_me"),
]
