from io import BytesIO
from datetime import timedelta
import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now
from celery import shared_task

from .models import Reservation
from booking.utils import make_qr_token, make_ics_token, build_reservation_ics


def _fmt_dt(dt):
    return dt.astimezone().strftime("%d.%m.%Y %H:%M")


@shared_task
def send_booking_created(reservation_id: int):
    r = Reservation.objects.get(pk=reservation_id)
    ctx = {
        "r": r,
        "datetime_start": _fmt_dt(r.datetime_start),
        "datetime_end": _fmt_dt(r.datetime_end),
    }
    subj = f"Заявка на бронирование получена — {ctx['datetime_start']}"
    body_txt = render_to_string("emails/booking_created.txt", ctx)
    msg = EmailMultiAlternatives(
        subj, body_txt, settings.DEFAULT_FROM_EMAIL, [r.email or settings.MANAGER_EMAIL]
    )
    msg.send()


@shared_task
def send_booking_confirmed(reservation_id: int):
    r = Reservation.objects.get(pk=reservation_id)
    token = make_qr_token(r.id)

    # QR-картинка
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # ICS-файл
    ics_text = build_reservation_ics(r)
    ics_bytes = ics_text.encode("utf-8")

    # Токен-ссылка для iCal (на случай клика)
    ics_token = make_ics_token(r.id)
    ics_link = f"{settings.SITE_BASE_URL}/api/ical?token={ics_token}"

    ctx = {
        "r": r,
        "datetime_start": _fmt_dt(r.datetime_start),
        "datetime_end": _fmt_dt(r.datetime_end),
        "table": f"{r.table.name} ({r.table.area.name})",
        "token": token,
        "ics_link": ics_link,
    }
    subj = f"Бронь подтверждена — {ctx['datetime_start']} — стол {r.table.name}"
    body_txt = render_to_string("emails/booking_confirmed.txt", ctx)

    msg = EmailMultiAlternatives(
        subj, body_txt, settings.DEFAULT_FROM_EMAIL, [r.email or settings.MANAGER_EMAIL]
    )
    msg.attach(filename=f"booking_{r.id}.png", content=buf.read(), mimetype="image/png")
    msg.attach(
        filename=f"booking_{r.id}.ics", content=ics_bytes, mimetype="text/calendar"
    )
    msg.send()


@shared_task
def send_booking_reminder(reservation_id: int):
    r = Reservation.objects.get(pk=reservation_id)
    ctx = {
        "r": r,
        "datetime_start": _fmt_dt(r.datetime_start),
        "datetime_end": _fmt_dt(r.datetime_end),
    }
    subj = f"Напоминание о бронировании — {ctx['datetime_start']}"
    body_txt = render_to_string("emails/booking_reminder.txt", ctx)
    msg = EmailMultiAlternatives(
        subj, body_txt, settings.DEFAULT_FROM_EMAIL, [r.email or settings.MANAGER_EMAIL]
    )
    msg.send()


@shared_task
def schedule_reminder(reservation_id: int, hours_before: int = 2):
    """Запланировать отправку напоминания за N часов до начала."""
    r = Reservation.objects.get(pk=reservation_id)
    eta = r.datetime_start - timedelta(hours=hours_before)
    if eta > now():
        send_booking_reminder.apply_async((reservation_id,), eta=eta)
