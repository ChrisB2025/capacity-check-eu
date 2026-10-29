"""Load runs saved by the engine's command line into the database.

``python manage.py import_runs <run_id> ...`` or ``--all``.
"""

from django.core.management.base import BaseCommand

from engine.pipeline import RUNS_DIR
from web.results import bridge


class Command(BaseCommand):
    help = "Import runs saved in data/processed/runs/."

    def add_arguments(self, parser):
        parser.add_argument("run_ids", nargs="*")
        parser.add_argument("--all", action="store_true")

    def handle(self, *args, **opts):
        ids = opts["run_ids"]
        if opts["all"]:
            ids = sorted(p.name for p in RUNS_DIR.iterdir() if p.is_dir())
        for rid in ids:
            run = bridge.import_saved(rid)
            self.stdout.write(f"{run.run_id} imported")
