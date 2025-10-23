from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from booking.models import Area


class Command(BaseCommand):
    help = "Recreate all default Areas with English names/descriptions and photos"

    def handle(self, *args, **kwargs):

        Area.objects.all().delete()
        self.stdout.write(self.style.WARNING("🧹 All existing Area entries deleted."))

        # 2. source images (the ones used in your template)
        src_dir = (
            Path(settings.BASE_DIR)
            / "booking"
            / "static"
            / "booking"
            / "img"
            / "restaurant_photo"
        )

        items = [
            {
                "name": "By the window",
                "description": "Soft daylight and a street view.",
                "file": "rest_photo_1.png",
                "order": 10,
            },
            {
                "name": "Center hall",
                "description": "Lively atmosphere in the heart of the restaurant.",
                "file": "rest_photo_2.png",
                "order": 20,
            },
            {
                "name": "Near the bar",
                "description": "Cozy bar vibe and quick access to drinks.",
                "file": "rest_photo_3.png",
                "order": 30,
            },
        ]

        created_total = 0
        for it in items:
            src_path = src_dir / it["file"]
            area = Area(
                name=it["name"],
                description=it["description"],
                order=it["order"],
                is_active=True,
            )

            if src_path.exists():
                area.photo.save(
                    src_path.name, ContentFile(src_path.read_bytes()), save=False
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ Photo not found: {src_path.name}")
                )

            area.save()
            created_total += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ {created_total} areas seeded successfully.")
        )
