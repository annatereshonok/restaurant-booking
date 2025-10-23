from decimal import Decimal
from pathlib import Path
from django.core.files import File
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import transaction, connection
from booking.models import Area, Table


RAW = [
    # ЛЕВЫЙ НИЗ
    {"id": 1, "name": "LW-2-1", "type": "2_horiz", "capacity": 2, "x": 25, "y": 94},
    {"id": 2, "name": "LW-2-2", "type": "2_horiz", "capacity": 2, "x": 34, "y": 94},
    {"id": 3, "name": "LW-2-3", "type": "2_horiz", "capacity": 2, "x": 43, "y": 94},
    # ЛЕВАЯ СЕРЕДИНА
    {"id": 3, "name": "LC-2-1", "type": "2_vert", "capacity": 2, "x": 15, "y": 42},
    # ЛЕВАЯ КОЛОННА 4-местных
    {"id": 5, "name": "LC-4-1", "type": "4", "capacity": 4, "x": 32, "y": 78},
    {"id": 6, "name": "LC-4-2", "type": "4", "capacity": 4, "x": 32, "y": 62},
    {"id": 7, "name": "LC-4-3", "type": "4", "capacity": 4, "x": 32, "y": 46},
    {"id": 8, "name": "LC-4-4", "type": "4", "capacity": 4, "x": 45, "y": 78},
    {"id": 9, "name": "LC-4-5", "type": "4", "capacity": 4, "x": 45, "y": 62},
    {"id": 10, "name": "LC-4-6", "type": "4", "capacity": 4, "x": 45, "y": 46},
    # ЦЕНТР 6-местные
    {"id": 11, "name": "CC-6-1", "type": "6", "capacity": 6, "x": 60, "y": 55},
    {"id": 12, "name": "CC-6-2", "type": "6", "capacity": 6, "x": 72, "y": 55},
    {"id": 13, "name": "CC-6-3", "type": "6", "capacity": 6, "x": 60, "y": 35},
    # ПРАВЫЙ ВЕРХ 2-местные
    {"id": 14, "name": "RC-2-1", "type": "2_horiz", "capacity": 2, "x": 55, "y": 15},
    {"id": 15, "name": "RC-2-2", "type": "2_horiz", "capacity": 2, "x": 65, "y": 15},
    # БАР (низ справа)
    {"id": 18, "name": "BAR-1", "type": "1", "capacity": 1, "x": 63, "y": 68},
    {"id": 19, "name": "BAR-2", "type": "1", "capacity": 1, "x": 67, "y": 68},
    {"id": 20, "name": "BAR-3", "type": "1", "capacity": 1, "x": 71, "y": 68},
    {"id": 21, "name": "BAR-4", "type": "1", "capacity": 1, "x": 75, "y": 68},
    {"id": 18, "name": "BAR-5", "type": "1", "capacity": 1, "x": 57, "y": 75},
    {"id": 19, "name": "BAR-6", "type": "1", "capacity": 1, "x": 57, "y": 82},
    {"id": 20, "name": "BAR-7", "type": "1", "capacity": 1, "x": 57, "y": 89},
    {"id": 21, "name": "BAR-8", "type": "1", "capacity": 1, "x": 57, "y": 96},
]


AREA_BY_PREFIX = {
    "BAR": "Near the bar",
    "C-": "Center hall",
    "W-": "By the window",
}
DEFAULT_AREA = "Center hall"


PHOTO_BY_TYPE = {
    "1": "booking/img/tables/table_type_1.svg",
    "2_horiz": "booking/img/tables/table_type_2_horiz.svg",
    "2_vert": "booking/img/tables/table_type_2_vert.svg",
    "4": "booking/img/tables/table_type_4.svg",
    "6": "booking/img/tables/table_type_6.svg",
}

PHOTO_BY_TYPE_NA = {
    "1": "booking/img/tables/table_type_1_NA.svg",
    "2_horiz": "booking/img/tables/table_type_2_horiz_NA.svg",
    "2_vert": "booking/img/tables/table_type_2_vert_NA.svg",
    "4": "booking/img/tables/table_type_4_NA.svg",
    "6": "booking/img/tables/table_type_6_NA.svg",
}


def area_name_for(table_name: str) -> str:
    n = (table_name or "").upper()
    for pref, a in AREA_BY_PREFIX.items():
        if n.startswith(pref):
            return a
    if "BAR" in n:
        return "Near the bar"
    return DEFAULT_AREA


def reset_sequences(*models):
    sql_list = connection.ops.sequence_reset_sql(no_style(), models)
    with connection.cursor() as c:
        for sql in sql_list:
            c.execute(sql)


def assign_photo_from_static(
    instance, *, field_name: str, static_map: dict, type_key: str, suffix: str = ""
):
    if not hasattr(instance, field_name):
        return
    field = getattr(instance, field_name)
    if field:
        return

    static_path = static_map.get(type_key)
    if not static_path:
        return

    abs_path = finders.find(static_path)
    if not abs_path:
        return

    ext = Path(static_path).suffix.lower() or ".png"
    safe = instance.name.lower().replace(" ", "_")
    with open(abs_path, "rb") as fh:
        getattr(instance, field_name).save(f"{safe}{suffix}{ext}", File(fh), save=True)


@transaction.atomic
class Command(BaseCommand):
    help = "Seed tables with coordinates and photos (by type). Supports --reset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all tables and their media files before seeding. Reset IDs.",
        )
        parser.add_argument(
            "--reset-areas",
            action="store_true",
            help="Additionally delete seed Areas (will be recreated).",
        )

    def _delete_table_files(self, t: Table):
        try:
            if getattr(t, "photo", None):
                t.photo.delete(save=False)
        except Exception:
            pass
        try:
            if getattr(t, "photo_inactive", None):
                t.photo_inactive.delete(save=False)
        except Exception:
            pass

    def handle(self, *args, **opts):
        # ----- RESET -----
        if opts.get("reset"):
            qs = Table.objects.all().only("id", "photo", "photo_inactive", "name")
            for t in qs:
                self._delete_table_files(t)
            Table.objects.all().delete()
            self.stdout.write(self.style.WARNING("🧹 Tables cleared (+ media)"))

            if opts.get("reset_areas"):
                names = set(AREA_BY_PREFIX.values()) | {DEFAULT_AREA}
                Area.objects.filter(name__in=names).delete()
                self.stdout.write(self.style.WARNING("🧹 Areas from seed set cleared"))

            reset_sequences(Table, Area)
            self.stdout.write(self.style.WARNING("🔁 Sequences reset"))

        area_cache = {}
        for nm in set(AREA_BY_PREFIX.values()) | {DEFAULT_AREA}:
            area_cache[nm], _ = Area.objects.get_or_create(
                name=nm, defaults={"is_active": True}
            )

        created, updated = 0, 0

        for row in RAW:
            name = row["name"].strip()
            table_type = row["type"].strip()
            x = Decimal(str(row["x"]))
            y = Decimal(str(row["y"]))
            capacity = int(row.get("capacity", 0))
            area = area_cache[area_name_for(name)]

            base, suffix = name, 2
            while Table.objects.filter(area=area, name=name).exists():
                name = f"{base}-{suffix}"
                suffix += 1

            obj, is_created = Table.objects.get_or_create(
                area=area,
                name=name,
                defaults={
                    "capacity": capacity,
                    "type": table_type,
                    "x": x,
                    "y": y,
                    "is_active": True,
                },
            )

            if not is_created:
                obj.capacity = capacity
                obj.type = table_type
                obj.x = x
                obj.y = y
                obj.is_active = True
                obj.save(update_fields=["capacity", "type", "x", "y", "is_active"])
                updated += 1
            else:
                created += 1

            if not obj.photo:
                assign_photo_from_static(
                    obj,
                    field_name="photo",
                    static_map=PHOTO_BY_TYPE,
                    type_key=table_type,
                    suffix="",
                )

            if not obj.photo_inactive:
                assign_photo_from_static(
                    obj,
                    field_name="photo_inactive",
                    static_map=PHOTO_BY_TYPE_NA,
                    type_key=table_type,
                    suffix="_NA",
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Tables seeded. Created: {created}, updated: {updated}"
            )
        )
