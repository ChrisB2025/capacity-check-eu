FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# output.css is pre-built and committed; there is no Tailwind step here.
# settings.py lets collectstatic run without DJANGO_SECRET_KEY.
RUN python manage.py collectstatic --noinput

# Data files live on the volume at DATA_DIR (/data); see README.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py ensure_shared_user && gunicorn web.wsgi --bind 0.0.0.0:${PORT:-8080} --workers=2 --timeout=180 --access-logfile -"]
