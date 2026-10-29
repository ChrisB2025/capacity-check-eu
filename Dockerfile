FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Phase 4 adds, following the mml-eu convention:
#   RUN python manage.py collectstatic --noinput   (SECRET_KEY guarded at build time)
#   and "python manage.py migrate --noinput &&" at the start of the CMD below.
# output.css is pre-built and committed; there is no Tailwind step here.

CMD ["sh", "-c", "gunicorn web.healthcheck:app --bind 0.0.0.0:${PORT:-8080} --workers=2 --timeout=120 --access-logfile -"]
