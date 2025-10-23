# HIKARI — система бронирования столиков ресторана

**HIKARI** — это веб‑приложение для онлайн‑бронирования столиков в ресторане.  
Гости могут выбрать зал и время, оформить бронь (в том числе без авторизации),  
а также управлять своими бронированиями через личный кабинет.  
Менеджеры ресторана видят список бронирований, подтверждают или отменяют их,  
и получают уведомления по электронной почте.

---

## Основной функционал

### Гость (пользователь)
- Регистрация и вход по **email + пароль**.
- Профиль с редактированием имени, телефона, аватара.
- История бронирований по статусам:
  - Ожидает подтверждения (pending)
  - Подтверждена (confirmed)
  - Гость на месте (seated)
  - Завершена (completed)
  - Отменена (canceled)
  - Не пришли (no_show)
- Возможность **отменить бронь**, если она в статусе `pending` или `confirmed`.
- Скачивание файла `.ics` (добавление в календарь).
- Форма бронирования с выбором стола, даты, времени и количества гостей.
- Анонимные бронирования (без регистрации).

### ‍Менеджер ресторана
- Панель менеджера (`/manager/`).
- Просмотр бронирований за день по залу.
- Подтверждение / отмена / изменение статуса брони.

### Почтовые уведомления
- Отправка писем о создании и подтверждении брони.
- Напоминания через **Celery + Redis**.
- Поддержка SMTP (Gmail).

### Интерфейс
- Django Templates + Tailwind CSS.
- Адаптивный дизайн.
- Цветовые метки для статусов брони.
- Вкладки по статусам в профиле пользователя.

---

## Технологии

- **Django 5.0+**, **Django REST Framework**
- **Celery**, **Redis**
- **PostgreSQL / SQLite**
- **Tailwind CDN**
- **Vanilla JS**
- **Docker Compose**

---

## 📂 Основная структура проекта

```
booking/
  api/views.py          # API эндпоинты для бронирований
  tasks.py              # фоновые задачи (email, напоминания)
  templates/booking/    # HTML‑шаблоны страниц бронирования
  static/booking/       # изображения, карты залов и т.д.

users/
  api/views.py          # эндпоинты авторизации и профиля
  templates/users/      # profile.html
  static/users/js/      # profile.js

config/
  settings.py
  celery.py
  urls.py
```

---

## Финальные URL

### Бронирование (`booking/api/urls.py`)
```
/api/availability/                            # Проверка доступности столов
/api/layout/tables/                           # Список столов
/api/layout/table-types/                      # Типы столов
/api/layout/areas/                            # Залы ресторана
/api/bookings/                                # Создание брони
/api/me/bookings-by-status/                   # Брони пользователя (по статусам)
/api/me/bookings/<id>/cancel                  # Отмена своей брони
/api/me/bookings/<id>/ical                    # Скачать .ics
/api/ical                                     # ICS по токену (публичный)

# Менеджерские эндпоинты
/api/manager/bookings/                        # Список броней за день
/api/manager/bookings/<id>/confirm            # Подтвердить бронь
/api/manager/bookings/<id>/cancel             # Отменить бронь
/api/manager/bookings/<id>/status             # Установить статус
/api/manager/statuses/                        # Доступные статусы
```

### Авторизация (`users/api/urls.py`)
```
/api/auth/register/     # Регистрация
/api/auth/login/        # Вход
/api/auth/logout/       # Выход
/api/auth/me/           # Получить данные профиля
/api/auth/me/update     # Обновить профиль
```

### Страницы (`booking/urls.py` + `users/urls.py`)
```
/                   — Главная страница
/booking/           — Страница бронирования
/profile/           — Личный кабинет пользователя
/manager/           — Панель менеджера (только staff)
```

---

## .env пример

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
ALLOWED_HOSTS=*
TIME_ZONE=Europe/Moscow

# BD
POSTGRES_DB=restaurant
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis / Celery
#REDIS_URL=redis://127.0.0.1:6379/0
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

SEED_ON_START=true
SEED_FORCE=true

# Booking rules
OPEN_TIME=12:00
CLOSE_TIME=22:00
VISIT_LENGTH_MIN=120
BUFFER_MIN=15

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
DEFAULT_FROM_EMAIL=
MANAGER_EMAIL=
SITE_BASE_URL=
EMAIL_TIMEOUT=20
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

---

## Запуск проекта

### Без Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Применяем миграции и создаем суперпользователя
python manage.py migrate
python manage.py createsuperuser

# Запускаем Redis
redis-server
```

#### Запускаем процессы:
```bash
# В одном терминале — сервер Django
python manage.py runserver

# В другом — Celery worker
celery -A config worker -l INFO

# В третьем — планировщик задач Celery Beat
celery -A config beat -l INFO
```

---

### Через Procfile (Honcho)

`Procfile`:
```
redis: redis-server
web: python manage.py runserver
worker: celery -A config worker -l INFO
beat: celery -A config beat -l INFO
```

Запуск:
```bash
pip install honcho
honcho start
```

---

### Через Docker Compose

```bash
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up -d
docker compose logs -f
```

После сборки проект будет доступен по адресу: **http://localhost/**

---

## Интерфейс
- `/` — главная.
- `/booking/` — выбор стола, даты, времени.
- `/profile/` — профиль пользователя, вкладки с бронями.
- `/manager/` — панель администратора.
- `/admin/` — стандартная админка Django.

---

## Лицензия

MIT (или укажи свою при необходимости).
