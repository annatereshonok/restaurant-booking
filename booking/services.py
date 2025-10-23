from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
from typing import Iterable, List, Optional, Tuple

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone

from booking.models import Table, Reservation


def parse_hhmm(value: str) -> time:
    hh, mm = value.split(":", 1)
    return time(int(hh), int(mm))


def combine(date_obj: date, t: time) -> datetime:
    naive = datetime(
        date_obj.year, date_obj.month, date_obj.day, t.hour, t.minute, t.second
    )
    return timezone.make_aware(naive, timezone.get_current_timezone())


def add_minutes(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.time()


def overlaps(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> bool:
    return a_start < b_end and b_start < a_end


OPEN_T: time = parse_hhmm(settings.OPEN_TIME)
CLOSE_T: time = parse_hhmm(settings.CLOSE_TIME)
VISIT_MIN: int = int(settings.VISIT_LENGTH_MIN)
BUFFER_MIN: int = int(settings.BUFFER_MIN)

if add_minutes(OPEN_T, VISIT_MIN) > CLOSE_T:
    raise ValueError(
        "VISIT_LENGTH_MIN больше рабочего окна. Проверьте OPEN_TIME/CLOSE_TIME."
    )


def generate_slots(visit_min: int = VISIT_MIN) -> List[Tuple[time, time]]:
    slots: List[Tuple[time, time]] = []
    start = OPEN_T
    step = visit_min + BUFFER_MIN
    while add_minutes(start, visit_min) <= CLOSE_T:
        end = add_minutes(start, visit_min)
        slots.append((start, end))
        start = add_minutes(start, step)
    return slots


def reservations_qs_for_table(table: Table, day: date) -> QuerySet[Reservation]:
    start_day = combine(day, time.min)
    end_day = combine(day, time.max)
    return Reservation.objects.filter(
        table=table,
        datetime_start__lt=end_day,
        datetime_end__gt=start_day,
        status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
    )


def table_is_free(table: Table, start_dt: datetime, end_dt: datetime) -> bool:
    return (
        not Reservation.objects.filter(
            table=table,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
        )
        .filter(Q(datetime_start__lt=end_dt) & Q(datetime_end__gt=start_dt))
        .exists()
    )


def nearest_after(table: Table, start_dt: datetime) -> Optional[datetime]:
    r = (
        Reservation.objects.filter(
            table=table,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
            datetime_start__gte=start_dt,
        )
        .order_by("datetime_start")
        .values_list("datetime_start", flat=True)
        .first()
    )
    return r


@dataclass
class AvailabilityInfo:
    table: Table
    available: bool
    available_until: Optional[datetime]


def availability_for_tables(
    day: date,
    start_time: time,
    guests: int,
    tables: Iterable[Table],
    visit_min: int = VISIT_MIN,
) -> List[AvailabilityInfo]:
    start_dt = combine(day, start_time)
    end_dt = start_dt + timedelta(minutes=visit_min)

    out: List[AvailabilityInfo] = []
    for table in tables:
        if table.capacity < guests or not table.is_active:
            out.append(AvailabilityInfo(table, False, None))
            continue

        free = table_is_free(table, start_dt, end_dt)
        if not free:
            out.append(AvailabilityInfo(table, False, None))
            continue

        nxt = nearest_after(table, start_dt)
        until_dt = None
        hard_close = combine(day, CLOSE_T)

        if nxt:
            until_candidate = nxt - timedelta(minutes=BUFFER_MIN)
            until_dt = min(until_candidate, hard_close)
        else:
            until_dt = hard_close

        out.append(AvailabilityInfo(table, True, until_dt))

    return out


@dataclass
class PickResult:
    table: Optional[Table]
    start_dt: datetime
    end_dt: datetime
    available_until: Optional[datetime]


def pick_table(
    day: date,
    start_time: time,
    guests: int,
    area_id: Optional[int] = None,
    visit_min: int = VISIT_MIN,
) -> PickResult:
    qs = Table.objects.filter(is_active=True, capacity__gte=guests)
    if area_id:
        qs = qs.filter(area_id=area_id)
    qs = qs.order_by("capacity", "id")

    start_dt = combine(day, start_time)
    end_dt = start_dt + timedelta(minutes=visit_min)

    for table in qs:
        if table_is_free(table, start_dt, end_dt):
            nxt = nearest_after(table, start_dt)
            hard_close = combine(day, CLOSE_T)
            if nxt:
                available_until = min(nxt - timedelta(minutes=BUFFER_MIN), hard_close)
            else:
                available_until = hard_close
            return PickResult(
                table=table,
                start_dt=start_dt,
                end_dt=end_dt,
                available_until=available_until,
            )

    return PickResult(
        table=None, start_dt=start_dt, end_dt=end_dt, available_until=None
    )
