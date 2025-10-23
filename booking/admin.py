from django.contrib import admin
from django.utils.html import format_html
from .models import Area, Table, Reservation


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "order", "thumb")
    list_editable = ("is_active", "order")
    search_fields = ("name", "description")

    def thumb(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:6px;">', obj.photo.url
            )
        return "—"

    thumb.short_description = "Photo"


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "area",
        "capacity",
        "type",
        "x",
        "y",
        "is_active",
        "thumb",
        "thumb_NA",
    )
    list_filter = ("area", "type", "is_active")
    search_fields = ("name",)
    autocomplete_fields = ("area",)

    def thumb(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:6px;">', obj.photo.url
            )
        return "—"

    thumb.short_description = "Photo"

    def thumb_NA(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:6px;">',
                obj.photo_inactive.url,
            )
        return "—"

    thumb_NA.short_description = "Photo NA"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "table",
        "datetime_start",
        "datetime_end",
        "guests",
        "status",
        "user",
        "name",
        "phone",
    )
    list_filter = ("status", "table__area", "table", "datetime_start")
    search_fields = ("name", "email", "phone")
    autocomplete_fields = ("table", "user")
    date_hierarchy = "datetime_start"
    actions = ["confirm_reservations", "cancel_reservations", "mark_seated"]

    @admin.action(description="Подтвердить выбранные брони")
    def confirm_reservations(self, request, queryset):
        updated = queryset.update(status=Reservation.Status.CONFIRMED)
        self.message_user(request, f"Подтверждено: {updated}")

    @admin.action(description="Отменить выбранные брони")
    def cancel_reservations(self, request, queryset):
        updated = queryset.update(status=Reservation.Status.CANCELED)
        self.message_user(request, f"Отменено: {updated}")

    @admin.action(description="Отметить как 'Гость на месте'")
    def mark_seated(self, request, queryset):
        updated = queryset.update(status=Reservation.Status.SEATED)
        self.message_user(request, f"Отмечено seated: {updated}")
