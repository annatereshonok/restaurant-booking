redis: redis-server
web: python manage.py runserver
worker: celery -A config worker -l INFO
beat: celery -A config beat -l INFO