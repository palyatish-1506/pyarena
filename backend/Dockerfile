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

# Apply migrations, then serve via ASGI (daphne) for HTTP + WebSockets.
# migrate is idempotent — safe on every boot. Render's Docker Command
# override must keep the migrate step (see render notes).
CMD ["sh", "-c", "python manage.py migrate --noinput && daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]
