# Capacity Check Europe (working name)

When the same public spending shock is applied in every EU member state, which industries does it press on, and are those industries already short of labour?

This repository tests whether open official EU data can answer that question. The standard shock is additional public spending equal to 1% of each member state's 2024 GDP, in one year, on housing and energy renovation, with the same composition of purchases in every country. It is an identical financial shock, not an identical physical programme.

The result locates pressure. It does not size price changes, it has no deficit or debt term, and it makes no claim about fiscal space for eurozone members. It cannot see constraints in permits, grid connections, planning or training capacity. Migration and posted workers are a named limitation.

## Status

| Phase | Content | State |
| :--- | :--- | :--- |
| 0 | Scaffold, Railway health check | Done, awaiting gate |
| 1 | Data acquisition, gate 1 | Not started |
| 2 | Model engine, gate 2 | Not started |
| 3 | EU-wide results, reviewer package | Not started |
| 4 | Web application | Not started |
| 5 | Sweden layer | Not started |
| 6 | AI drafting features | Not started |
| 7 | Report and handover | Not started |

No results exist yet. Every published number will be traceable to a dataset, edition and checksum in `docs/data-register.md`.

## Layout

```
docs/       specification, CDM baseline, method note, data register, decisions, gate reports
data/raw/   downloaded files, never edited (not committed; rebuilt by `python -m engine fetch`)
data/processed/  parquet files written by the engine (not committed)
engine/     plain Python package, no Django; reproduces every number from the command line
tests/      pytest, including the fixed test set of runs
web/        Django app from Phase 4; until then a health check only
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
```

## Reproducing a result

From Phase 2 onward:

```bash
python -m engine fetch
python -m engine run --shock 1.0 --edition 2026
```

## Hosting

Railway project `capacity-check-eu`, separate from every other MML EU or US service. Public URL: https://web-production-d723d.up.railway.app (health check only until Phase 4).

| Service | Role |
| :--- | :--- |
| `web` | Built from this repository's Dockerfile on every push to `main`. Health check at `/health/`. Volume `web-data` mounted at `/data`. |
| `Postgres` | Railway PostgreSQL. Used from Phase 4. |

Variables on `web` (values live only in Railway, never in the repository):

| Variable | Purpose |
| :--- | :--- |
| `DJANGO_SECRET_KEY` | Django secret, required at runtime from Phase 4, not at build time |
| `DATABASE_URL` | Reference to the `Postgres` service |
| `DATA_DIR` | `/data`, the volume holding raw and processed data files |
| `PUBLIC_READ_ONLY` | `false` until reviewer sign-off; `true` opens read-only public access |
| `ALLOWED_HOSTS` | The Railway domain |
| `ANTHROPIC_API_KEY` | Used from Phase 6 only. Set a monthly spend cap in the Anthropic console; the code will also enforce a cap. |

Local development uses PostgreSQL 17 on the developer's machine, database `capacity_check_eu`. Copy `.env.example` to `.env`.

## Licence

Code under the MIT Licence. Documents and results tables under CC BY 4.0. Source data remain under their publishers' terms; see `LICENCE` and `docs/data-register.md`.
