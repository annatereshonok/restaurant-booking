from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create a default superuser (if not exists)"

    def handle(self, *args, **options):
        email = "admin@example.com"
        password = "admin123"
        first_name = "Admin"
        phone = "+79999999999"

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                phone=phone,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser created: {email} / {password}")
            )
        else:
            self.stdout.write(self.style.WARNING(f"Superuser already exists: {email}"))
