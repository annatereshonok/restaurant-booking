from datetime import date, timedelta, datetime
from typing import Optional
from rest_framework import serializers

from booking.models import Reservation, Table, Area
from booking.services import parse_hhmm, combine, table_is_free, pick_table, VISIT_MIN


class AreaSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Area
        fields = ("id", "name", "description", "photo_url", "is_active", "order")

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and hasattr(obj.photo, "url"):
            return (
                request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
            )
        return None


class TableSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    photo_inactive_url = serializers.SerializerMethodField()
    area_name = serializers.CharField(source="area.name", read_only=True)

    class Meta:
        model = Table
        fields = (
            "id",
            "name",
            "capacity",
            "x",
            "y",
            "type",
            "is_active",
            "area",
            "area_name",
            "photo_url",
            "photo_inactive_url",
        )

    def get_photo_url(self, obj):
        req = self.context.get("request")
        if obj.photo and hasattr(obj.photo, "url"):
            return req.build_absolute_uri(obj.photo.url) if req else obj.photo.url
        return None

    def get_photo_inactive_url(self, obj):
        req = self.context.get("request")
        if obj.photo_inactive and hasattr(obj.photo_inactive, "url"):
            return (
                req.build_absolute_uri(obj.photo_inactive.url)
                if req
                else obj.photo_inactive.url
            )
        return None


class ReservationListSerializer(serializers.ModelSerializer):
    table_name = serializers.CharField(source="table.name", read_only=True)
    area_id = serializers.IntegerField(source="table.area_id", read_only=True)
    table_area = serializers.CharField(source="table.area.name", read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "id",
            "status",
            "datetime_start",
            "datetime_end",
            "guests",
            "table",
            "table_name",
            "area_id",
            "table_area",
            "name",
            "phone",
            "email",
            "comment",
            "created_at",
        )
        read_only_fields = fields


class ReservationCreateSerializer(serializers.Serializer):
    date = serializers.DateField()
    start = serializers.CharField()  # HH:MM
    guests = serializers.IntegerField(min_value=1)
    table_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    duration_min = serializers.IntegerField(required=False, min_value=30, max_value=360)

    def validate(self, attrs):
        # Парсим время
        try:
            start_t = parse_hhmm(attrs["start"])
        except Exception:
            raise serializers.ValidationError({"start": "Формат времени HH:MM"})

        day: date = attrs["date"]
        guests: int = attrs["guests"]
        req = self.context["request"]
        user = getattr(req, "user", None)
        table_id = attrs.get("table_id")

        visit_min = attrs.get("duration_min") or VISIT_MIN
        start_dt = combine(day, start_t)
        end_dt = start_dt + timedelta(minutes=visit_min)

        # Если table_id есть — проверим существование
        table: Optional[Table] = None
        if table_id:
            try:
                table = Table.objects.get(pk=table_id, is_active=True)
            except Table.DoesNotExist:
                raise serializers.ValidationError(
                    {"table_id": "Table is not found or inactive"}
                )
            if table.capacity < guests:
                raise serializers.ValidationError(
                    {"guests": "The number of guests is higher than table capacity"}
                )

            if not table_is_free(table, start_dt, end_dt):
                raise serializers.ValidationError({"table_id": "The table is reserved"})
        else:
            pick = pick_table(day, start_t, guests, area_id=None, visit_min=visit_min)
            if not pick.table:
                raise serializers.ValidationError(
                    {"non_field_errors": ["No available time slots for this table"]}
                )
            table = pick.table  # type: ignore

        attrs["start_dt"] = start_dt
        attrs["end_dt"] = end_dt
        attrs["table_obj"] = table
        attrs["visit_min"] = visit_min

        if not (user and user.is_authenticated):
            name = attrs.get("name", "").strip()
            phone = attrs.get("phone", "").strip()
            email = attrs.get("email", "").strip()
            if not name:
                raise serializers.ValidationError({"name": "Please provide your name"})
            if not (phone or email):
                raise serializers.ValidationError(
                    {
                        "phone": "Email or phone is needed",
                        "email": "Email or phone is needed",
                    }
                )

        return attrs

    def create(self, validated_data):
        req = self.context["request"]
        user = req.user if req.user.is_authenticated else None

        table: Table = validated_data["table_obj"]
        start_dt: datetime = validated_data["start_dt"]
        end_dt: datetime = validated_data["end_dt"]

        name = validated_data.get("name") or (
            getattr(user, "first_name", "") or getattr(user, "email", "Гость")
        )
        phone = validated_data.get("phone") or getattr(user, "phone", "")
        email = validated_data.get("email") or getattr(user, "email", "")

        reservation = Reservation.objects.create(
            user=user,
            table=table,
            datetime_start=start_dt,
            datetime_end=end_dt,
            guests=validated_data["guests"],
            name=name,
            phone=phone,
            email=email,
            comment=validated_data.get("comment", ""),
            status=Reservation.Status.PENDING,
        )
        return reservation


class ManagerBookingListItem(serializers.ModelSerializer):
    table_name = serializers.CharField(source="table.name", read_only=True)
    area = serializers.CharField(source="table.area.name", read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "id",
            "status",
            "datetime_start",
            "datetime_end",
            "guests",
            "table",
            "table_name",
            "area",
            "name",
            "phone",
            "email",
            "comment",
        )
