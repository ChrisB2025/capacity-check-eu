# Gate 0 report: scaffold

Date: 2026-10-29. Gate question: do you confirm the layout and the licence?

## What exists

**Repository.** Public at https://github.com/ChrisB2025/capacity-check-eu, branch `main`. The layout follows the build brief. The engine modules are stubs with docstrings and no calculations. `python -m engine fetch --dry-run` lists the fourteen planned sources; `python -m engine run` refuses to run until Phase 2. Tests, ruff and black pass, and pre-commit runs both.

**Railway.** Project `capacity-check-eu` (ID `41b122bf-a23d-4c97-825a-536b0aa58627`), environment `production`.

| Resource | Name | Notes |
| :--- | :--- | :--- |
| Web service | `web` | Built from the Dockerfile on every push to `main`. Domain `web-production-d723d.up.railway.app`. Health check at `/health/`. |
| Database | `Postgres` | Railway PostgreSQL. Unused until Phase 4. |
| Volume | `web-data` | Mounted on `web` at `/data`. |

Variables on `web`: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DATA_DIR`, `PUBLIC_READ_ONLY`, `ALLOWED_HOSTS`, `ANTHROPIC_API_KEY`. Values are held only in Railway.

**Licence.** MIT for code, CC BY 4.0 for documents and results, as decided. The copyright line reads "the Capacity Check Europe contributors".

## Departures from the brief, for your confirmation

1. **The Dockerfile has no collectstatic or migrate step yet.** There is no Django project before Phase 4, so the image serves a one-file health check through gunicorn. The Dockerfile marks where both steps go in Phase 4.
2. **`docs/ciaran-briefing.md` is not committed.** It is not in the brief's layout and links to private documents. It stays on your machine, excluded locally from git.
3. **The FIGARO parser is our own,** not pymrio or MARIO as spec-v1 names. The evidence is in `docs/decisions.md`.
4. **This report is a separate file,** named to match the later gate reports.

## Things you need to do

1. **Replace `ANTHROPIC_API_KEY` on the Railway `web` service.** It holds a placeholder, `replace-me-phase-6`. Set a monthly spend cap in the Anthropic console when you add the real key.
2. **Create the local development database.** The local PostgreSQL 17 service asks for a password, which this session does not have. Run this once:

   ```bash
   "/c/Program Files/PostgreSQL/17/bin/createdb" -U postgres -h localhost capacity_check_eu
   ```

3. **Decide the name and the copyright holder** when ready. Nothing depends on either before Phase 4.

## Risks found while scaffolding

- **`railway.toml` is deprecated.** Railway says config-as-code files stop working on 1 December 2026, which falls inside the project. The same build and health-check settings are now also set on the service itself, so the deploy keeps working after that date. Removing `railway.toml` or migrating to Railway's new format is a choice for you; I recommend removing it before December and relying on the service settings.
- **Region.** Railway placed `web` and its volume in `us-west2` by default. Nothing personal is stored, so this is not a data-protection issue, but an EU region suits the project. Moving is easiest now, while the volume is empty. I recommend `europe-west4`; say if you want it.
- **Previous FIGARO edition.** Gate 1 depends on the 2025 edition still being in CIRCABC. CIRCABC cannot be listed from a script, so this may need a manual browser download in Phase 1.

## Open items carried to Phase 1

- Check the CIRCABC 2025 edition folder is live and download both editions.
- Save the Irish Fiscal Advisory Council PDF by hand; it refuses scripted downloads.
- Confirm licences for the DG ECFIN files, Konjunkturinstitutet and the ELA report.
- Read the German QuBe report, BMAS FB 683, before any claim of novelty.
