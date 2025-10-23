from django.urls import path
from users.views import profile_page

urlpatterns = [
    path("profile/", profile_page, name="profile_page"),
]
