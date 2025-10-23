from django.conf import settings
from django.core import signing
from django.utils import timezone

QR_SALT = "rb.qr.v1"
ICS_SALT = "rb.ics.v1"


def make_qr_token(reservation_id: int) -> str:
    """Подписанный токен для QR (включает id)."""
    return signing.dumps({"rid": reservation_id}, salt=QR_SALT)


def verify_qr_token(token: str) -> int:
    """Вернёт reservation_id или бросит BadSignature/SignatureExpired."""
    data = signing.loads(token, salt=QR_SALT, max_age=60 * 60 * 24 * 7)
    return int(data["rid"])


def booking_url(reservation_id: int) -> str:
    return (
        f"{settings.SITE_BASE_URL}/admin/booking/reservation/{reservation_id}/change/"
    )


def make_ics_token(reservation_id: int) -> str:
    return signing.dumps({"rid": reservation_id}, salt=ICS_SALT)


def verify_ics_token(token: str) -> int:
    data = signing.loads(token, salt=ICS_SALT, max_age=60 * 60 * 24 * 30)
    return int(data["rid"])


def _ics_dt(dt) -> str:
    """Формат ICS локализованного времени: YYYYMMDDTHHMMSS (с TZID будет норм)."""
    return dt.astimezone().strftime("%Y%m%dT%H%M%S")


def _ics_escape(s: str) -> str:
    return (
        (s or "")
        .replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def build_reservation_ics(r) -> str:
    tzid = settings.TIME_ZONE
    uid = f"restobooker-{r.id}@{settings.SITE_BASE_URL.replace('http://', '').replace('https://', '')}"
    stamp = _ics_dt(timezone.now())
    start = _ics_dt(r.datetime_start)
    end = _ics_dt(r.datetime_end)
    summary = f"Бронь стола {r.table.name} ({r.table.area.name})"
    location = _ics_escape(f"{r.table.area.name} — стол {r.table.name}")
    description = _ics_escape(
        f"Гостей: {r.guests}. Контакт: {r.name} {r.phone or ''} {r.email or ''}."
    )
    url = booking_url(r.id)

    ics = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//RestoBooker//RU",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP;TZID={tzid}:{stamp}",
            f"DTSTART;TZID={tzid}:{start}",
            f"DTEND;TZID={tzid}:{end}",
            f"SUMMARY:{_ics_escape(summary)}",
            f"LOCATION:{location}",
            f"DESCRIPTION:{description}\\n{_ics_escape(url)}",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )
    return ics
