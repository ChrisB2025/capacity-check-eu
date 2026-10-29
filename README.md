# Capacity Check Europe (working name)

When the same public spending shock is applied in every EU member state, which industries does it press on, and are those industries already short of labour?

This repository tests whether open official EU data can answer that question. The standard shock is additional public spending equal to 1% of each member state's 2024 GDP, in one year, on housing and energy renovation, with the same composition of purchases in every country. It is an identical financial shock, not an identical physical programme.

The result locates pressure. It does not size price changes, it has no deficit or debt term, and it makes no claim about fiscal space for eurozone members. It cannot see constraints in permits, grid connections, planning or training capacity. Migration and posted workers are a named limitation.

## Status

| Phase | Content | State |
| :--- | :--- | :--- |
| 0 | Scaffold, Railway health check | Done |
| 1 | Data acquisition, gate 1 | Report written; previous FIGARO edition requested from Eurostat |
| 2 | Model engine, gate 2 | Done; composition table and method note with the reviewer |
| 3 | EU-wide results, reviewer package | Provisional results; gate 3 report written |
| 4 | Web application | Built and deployed behind a shared login |
| 5 | Sweden layer | Provisional results; Sweden page in the web app |
| 6 | AI drafting features | Not started |
| 7 | Report and handover | Not started |

All results so far are **provisional**: they use compositions not yet confirmed after review. Every number is traceable to a dataset, edition and checksum in `docs/data-register.md` and each run's manifest.

## Layout

```
docs/       specification, CDM baseline, method note, data register, decisions, gate reports
data/raw/   downloaded files, never edited (not committed; rebuilt by `python -m engine fetch`)
data/processed/  parquet files written by the engine (not committed)
engine/     plain Python package, no Django; reproduces every number from the command line
  concordances/  industry concordance, generated and committed
tests/      pytest, including the fixed test set of runs
web/        Django app: calls the engine, stores its tables, computes nothing itself
notebooks/  exploratory, not load-bearing
```

## Setup

Python 3.11 or later.

```bash
python -m venv .venv
source .venv/Scripts/activate      # Git Bash on Windows; .venv/bin/activate elsewhere
pip install -r requirements-dev.txt
pre-commit install
pytest
python -m engine fetch --dry-run   # lists every planned source
python -m engine fetch             # downloads, parses and validates every source
python -m engine gate1             # rebuilds the gate 1 coverage tables
```

## Reproducing a result

From Phase 2 onward:

```bash
python -m engine fetch
python -m engine run --shock 1.0 --edition 2026     # one run; add --provisional until a composition is confirmed
python -m engine results                           # the full matrix and docs/results/
```

The web app locally (SQLite when `DATABASE_URL` is unset):

```bash
DJANGO_DEBUG=1 python manage.py migrate
DJANGO_DEBUG=1 python manage.py import_runs --all
DJANGO_DEBUG=1 python manage.py runserver
```

`npm install && npm run css` rebuilds the committed Tailwind file after template changes.

## Hosting

Railway project `capacity-check-eu`, separate from every other MML EU or US service. Public URL: https://web-production-d723d.up.railway.app (shared login until reviewer sign-off).

| Service | Role |
| :--- | :--- |
| `web` | Built from this repository's Dockerfile on every push to `main`. Health check at `/health/`. Volume `web-data` mounted at `/data`. |
| `Postgres` | Railway PostgreSQL: runs, result rows and the CDM tables. |

Variables on `web` (values live only in Railway, never in the repository):

| Variable | Purpose |
| :--- | :--- |
| `DJANGO_SECRET_KEY` | Django secret, required at runtime from Phase 4, not at build time |
| `DATABASE_URL` | Reference to the `Postgres` service |
| `DATA_DIR` | `/data`, the volume holding raw and processed data files |
| `PUBLIC_READ_ONLY` | `false` until reviewer sign-off; `true` opens read-only public access |
| `ALLOWED_HOSTS` | The Railway domain |
| `APP_USERNAME`, `APP_PASSWORD` | The single shared login, created at each start |
| `ANTHROPIC_API_KEY` | Used from Phase 6 only. Set a monthly spend cap in the Anthropic console; the code will also enforce a cap. |

Local development uses SQLite unless `DATABASE_URL` points at PostgreSQL. The data files on the volume were copied from the development machine, so production runs read files with the same checksums.

## Licence

Code under the MIT Licence. Documents and results tables under CC BY 4.0. Source data remain under their publishers' terms; see `LICENCE` and `docs/data-register.md`.
