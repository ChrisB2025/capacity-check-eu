# web

The Django application (Phase 4). It calls the engine and stores each run's
tables unchanged; it computes nothing itself.

- `settings.py`, `urls.py`, `wsgi.py`: the project. `manage.py` is at the repository root.
- `results/`: runs, inputs page, results pages, CSV downloads, the shared login.
- `cdm/`: the seven Canonical Data Model v1.6.2 tables, mirroring the baseline's field names.
- `static/css/output.css`: Tailwind, pre-compiled and committed (`npm run css`).
- `static/js/htmx.min.js`: HTMX 1.9.12, vendored.
- `tools/build_map.py`: builds the map outlines from Eurostat GISCO boundaries.

Run locally (SQLite when `DATABASE_URL` is unset):

```
set DJANGO_DEBUG=1
python manage.py migrate
python manage.py import_runs --all
python manage.py runserver
```
