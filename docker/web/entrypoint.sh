#!/usr/bin/env bash
set -e

python manage.py collectstatic --noinput || true
python manage.py migrate --noinput


if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "Seeding demo data (prod)..."
  if [ "${SEED_FORCE:-false}" = "true" ]; then
    python manage.py seed_su || true
    python manage.py seed_areas || true
    python manage.py seed_table --reset
  else
    python manage.py seed || true
  fi
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60
