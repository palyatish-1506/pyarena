# Backend image for Render (and local `docker build` sanity checks).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files at build time so whitenoise can serve them.
# A throwaway SECRET_KEY satisfies prod's boot check; env vars aren't needed
# for collectstatic itself.
RUN SECRET_KEY=build-time-dummy DJANGO_SETTINGS_MODULE=config.settings.prod \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Apply migrations, then serve. migrate is idempotent — safe on every boot.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
