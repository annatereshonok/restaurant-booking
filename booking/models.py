from django.conf import settings
from django.db import models


class Area(models.Model):
    """Зона/зал: основной зал, терраса, окна и т.д."""

    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to="areas/", blank=True)  # превью зоны
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Table(models.Model):
    class IconType(models.TextChoices):
        ONE = "1", "1 seat"
        T2_HORIZ = "2_horiz", "2 seats (horiz)"
        T2_VERT = "2_vert", "2 seats (vert)"
        FOUR = "4", "4 seats"
        SIX = "6", "6 seats"

    area = models.ForeignKey(
        "booking.Area", on_delete=models.PROTECT, related_name="tables"
    )
    name = models.CharField(max_length=32)
    capacity = models.PositiveSmallIntegerField()
    type = models.CharField(
        max_length=16, choices=IconType.choices, default=IconType.FOUR
    )

    x = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    y = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    photo = models.ImageField(upload_to="tables/", blank=True, null=True)
    photo_inactive = models.ImageField(
        upload_to="tables/inactive/", blank=True, null=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("area", "name")
        ordering = ["area__name", "name"]

    def __str__(self) -> str:
        return f"{self.area}: {self.name} ({self.capacity})"


class Reservation(models.Model):
    """Бронь столика на интервал времени."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает подтверждения"
        CONFIRMED = "confirmed", "Подтверждена"
        CANCELED = "canceled", "Отменена"
        SEATED = "seated", "Гость на месте"
        COMPLETED = "completed", "Завершена"
        NO_SHOW = "no_show", "Не пришли"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
        help_text="Владелец брони (может быть пусто для анонимной заявки).",
    )
    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name="reservations"
    )

    datetime_start = models.DateTimeField()
    datetime_end = models.DateTimeField()

    guests = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=128)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-datetime_start", "-created_at"]
        indexes = [
            models.Index(fields=["table", "datetime_start"]),
            models.Index(fields=["table", "datetime_end"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.table} — {self.datetime_start:%Y-%m-%d %H:%M}→" \
               f"{self.datetime_end:%H:%M} [{self.get_status_display()}]"
