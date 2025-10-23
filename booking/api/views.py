from datetime import date
from typing import Optional

from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import localdate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from booking.models import Area, Table, Reservation
from .serializers import (
    AreaSerializer,
    TableSerializer,
    ReservationListSerializer,
    ReservationCreateSerializer,
    ManagerBookingListItem,
)
from booking.services import availability_for_tables, parse_hhmm
from booking.tasks import (
    send_booking_created,
    send_booking_confirmed,
    schedule_reminder,
)
from booking.utils import verify_ics_token, build_reservation_ics


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


class AreaListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = AreaSerializer

    def get_queryset(self):
        qs = Area.objects.filter(is_active=True).order_by("order", "name")
        return qs


@api_view(["GET"])
@permission_classes([AllowAny])
def tables_list(request):
    qs = Table.objects.filter(is_active=True).order_by("area__name", "name")
    area = request.query_params.get("area")
    if area:
        qs = qs.filter(area_id=area)
    return Response(TableSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def table_types(request):
    types = (
        Table.objects.filter(is_active=True)
        .values_list("type", flat=True)
        .distinct()
        .order_by()
    )
    labels = dict(Table.TableType.choices)
    return Response([{"code": t, "name": labels.get(t, t)} for t in types])


@api_view(["GET"])
@permission_classes([AllowAny])
def availability(request):
    d = request.query_params.get("date")
    start = request.query_params.get("start")
    guests = request.query_params.get("guests")
    area = request.query_params.get("area")
    duration = request.query_params.get("duration")
    ttype = request.query_params.get("type")

    if not d or not start or not guests:
        return Response(
            {"detail": "date, start, guests обязательны"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        day = _parse_date(d)
        start_t = parse_hhmm(start)
        guests_i = int(guests)
    except Exception:
        return Response(
            {"detail": "Некорректные параметры (формат date=start=guests)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = Table.objects.filter(is_active=True, capacity__gte=guests_i)
    if area:
        qs = qs.filter(area_id=area)
    if ttype:
        qs = qs.filter(type=ttype)

    visit_min = int(duration) if duration else None
    info = availability_for_tables(
        day, start_t, guests_i, qs, visit_min=visit_min if visit_min else None
    )
    out = []
    for it in info:
        au: Optional[str] = (
            it.available_until.strftime("%H:%M")
            if (it.available and it.available_until)
            else None
        )
        out.append(
            {
                "id": it.table.pk,
                "name": it.table.name,
                "capacity": it.table.capacity,
                "type": it.table.type,
                "x": float(it.table.x),
                "y": float(it.table.y),
                "available": it.available,
                "available_until": au,
            }
        )

    return Response(
        {
            "date": d,
            "start": start,
            "guests": guests_i,
            "area": int(area) if area else None,
            "duration": visit_min if visit_min else None,
            "tables": out,
        }
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def my_booking_cancel(request, pk: int):
    r = Reservation.objects.filter(pk=pk, user=request.user).first()
    if not r:
        return Response(
            {"detail": "Бронь не найдена"}, status=status.HTTP_404_NOT_FOUND
        )

    if r.status == Reservation.Status.CANCELED:
        return Response({"detail": "Уже отменена"}, status=status.HTTP_400_BAD_REQUEST)

    if r.status not in [Reservation.Status.PENDING, Reservation.Status.CONFIRMED]:
        return Response(
            {"detail": "Эту бронь нельзя отменить"}, status=status.HTTP_400_BAD_REQUEST
        )

    r.status = Reservation.Status.CANCELED
    r.save(update_fields=["status"])
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bookings_by_status(request):
    qs = Reservation.objects.filter(user=request.user).order_by("-datetime_start")

    counts = {}
    by_status = {}
    for code, _ in Reservation.Status.choices:
        sub = qs.filter(status=code)
        counts[code] = sub.count()
        by_status[code] = ReservationListSerializer(sub, many=True).data

    return Response(
        {
            "counts": counts,
            "by_status": by_status,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_booking(request):
    serializer = ReservationCreateSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    send_booking_created.delay(obj.id)
    return Response(ReservationListSerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manager_confirm(request, pk: int):
    r = Reservation.objects.filter(pk=pk).first()
    if not r:
        return Response({"detail": "Не найдено"}, status=404)
    if r.status == Reservation.Status.CANCELED:
        return Response({"detail": "Бронь отменена"}, status=400)
    r.status = Reservation.Status.CONFIRMED
    r.save(update_fields=["status"])
    send_booking_confirmed.delay(r.id)
    schedule_reminder.delay(r.id, hours_before=2)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manager_cancel(request, pk: int):
    r = Reservation.objects.filter(pk=pk).first()
    if not r:
        return Response({"detail": "Не найдено"}, status=404)
    r.status = Reservation.Status.CANCELED
    r.save(update_fields=["status"])
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_status_choices(request):
    data = [{"code": c, "label": l} for c, l in Reservation.Status.choices]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def manager_bookings_list(request):
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    statuses = request.query_params.getlist("status")

    qs = Reservation.objects.select_related("table", "table__area", "user").order_by(
        "datetime_start"
    )

    if date_from:
        try:
            qs = qs.filter(datetime_start__date__gte=date.fromisoformat(date_from))
        except Exception:
            return Response({"detail": "Некорректный date_from"}, status=400)
    if date_to:
        try:
            qs = qs.filter(datetime_start__date__lte=date.fromisoformat(date_to))
        except Exception:
            return Response({"detail": "Некорректный date_to"}, status=400)
    if statuses:
        qs = qs.filter(status__in=statuses)

    table = request.query_params.get("table")
    if table:
        qs = qs.filter(table_id=table)
    area = request.query_params.get("area")
    if area:
        qs = qs.filter(table__area_id=area)
    user = request.query_params.get("user")
    if user:
        qs = qs.filter(user_id=user)

    data = [ManagerBookingListItem(r).data for r in qs]
    return Response({"count": len(data), "results": data})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def manager_set_status(request, pk: int):
    r = Reservation.objects.filter(pk=pk).first()
    if not r:
        return Response({"detail": "Бронь не найдена"}, status=404)

    new_status = request.data.get("status")
    allowed = {code for code, _ in Reservation.Status.choices}
    if new_status not in allowed:
        return Response({"detail": "Недопустимый статус"}, status=400)

    prev = r.status
    r.status = new_status
    r.save(update_fields=["status"])

    if (
        new_status == Reservation.Status.CONFIRMED
        and prev != Reservation.Status.CONFIRMED
    ):
        send_booking_confirmed.delay(r.id)  # <- письмо с QR
        schedule_reminder.delay(r.id, hours_before=2)

    return Response({"ok": True, "id": r.id, "status": r.status})


def _get_day(param: Optional[str]):
    if not param:
        return localdate()
    d = parse_date(param)
    return d or localdate()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_booking_get(request, pk: int):
    r = Reservation.objects.filter(pk=pk, user=request.user).first()
    if not r:
        return Response({"detail": "Бронь не найдена"}, status=404)
    return Response(ReservationListSerializer(r).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_booking_ical(request, pk: int):
    r = Reservation.objects.filter(pk=pk, user=request.user).first()
    if not r:
        return Response({"detail": "Бронь не найдена"}, status=404)
    ics = build_reservation_ics(r)
    resp = HttpResponse(ics, content_type="text/calendar; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="booking_{r.id}.ics"'
    return resp


@api_view(["GET"])
@permission_classes([AllowAny])
def booking_ical_by_token(request):
    token = request.query_params.get("token")
    if not token:
        return Response({"detail": "token обязателен"}, status=400)
    try:
        rid = verify_ics_token(token)
    except Exception:
        return Response({"detail": "Неверный или истекший токен"}, status=400)
    r = Reservation.objects.filter(pk=rid).first()
    if not r:
        return Response({"detail": "Бронь не найдена"}, status=404)
    ics = build_reservation_ics(r)
    resp = HttpResponse(ics, content_type="text/calendar; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="booking_{r.id}.ics"'
    return resp
