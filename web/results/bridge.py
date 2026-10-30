"""The only place the web app calls the engine.

``execute`` runs the engine with the parameters from the inputs page, saves the
run as the command line does, and stores every row of every engine table in
the database unchanged. No figure is computed here.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime

import yaml
from django.db import transaction

from engine import cdm, pipeline, results, shock, sweden
from engine.params import RunParams
from engine.rating import NO_RATING
from engine.sources._common import DATA_DIR, PROCESSED_DIR
from web.cdm.models import MODELS
from web.results.models import (
    CompositionTable,
    DataEdition,
    RequirementExtension,
    ResultRow,
    Run,
    RunInput,
)

USER_COMPOSITIONS = DATA_DIR / "compositions"
SWEDEN = "SE"


def editions() -> list[tuple[str, int]]:
    """FIGARO editions and reference years with a cached model."""
    out = []
    for f in sorted(PROCESSED_DIR.glob("leontief_*_y*.json")):
        _, ed, year = f.stem.split("_")
        out.append((ed, int(year[1:])))
    return out


def compositions() -> dict[str, shock.Composition]:
    return {
        p.stem: shock.load_composition(p.stem)
        for p in sorted(shock.COMPOSITION_DIR.glob("*.yaml"))
    }


def user_composition(base: shock.Composition, shares: dict[str, float]) -> str:
    """Write an edited composition and return its path for the engine."""
    lines = [
        {"code": ln.code, "share": shares[ln.code], "label": ln.label}
        for ln in base.lines
        if shares.get(ln.code, 0) > 0
    ]
    body = {
        "name": "user-defined",
        "status": "user-defined",
        "confirmed_by": None,
        "confirmed_on": None,
        "description": f"Edited from '{base.name}' on the inputs page.",
        "lines": lines,
    }
    text = yaml.safe_dump(body, sort_keys=False)
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    USER_COMPOSITIONS.mkdir(parents=True, exist_ok=True)
    path = USER_COMPOSITIONS / f"user-{digest}.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def _clean(v):
    """JSON-safe value: NaN becomes None, numpy scalars become Python."""
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _rows(df) -> list[dict]:
    return [
        {k: _clean(v) for k, v in rec.items()} for rec in df.to_dict(orient="records")
    ]


def execute(params: RunParams) -> Run:
    existing = Run.objects.filter(run_id=_peek_id(params)).first()
    if existing:
        return existing
    start = time.perf_counter()
    res = pipeline.run(params, allow_unconfirmed=True)
    pipeline.save(res)
    tables = engine_tables(res)
    seconds = time.perf_counter() - start
    return store(res, tables, seconds)


def _peek_id(params: RunParams) -> str | None:
    # The run id depends on data checksums, known only after a run; a saved
    # run with identical parameters is found by its stored parameters instead.
    for run in Run.objects.filter(params=json.loads(json.dumps(params.as_dict()))):
        return run.run_id
    return None


@transaction.atomic
def store(res, tables: dict, seconds: float | None = None) -> Run:
    m = res.manifest
    comp_src = next(s for s in m["sources"] if s["role"] == "composition")
    comp_obj = shock.load_composition(res.params.composition)
    comp, _ = CompositionTable.objects.get_or_create(
        sha256=comp_src["sha256"],
        defaults={
            "name": comp_obj.name,
            "status": comp_obj.status,
            "confirmed_by": comp_obj.confirmed_by,
            "confirmed_on": comp_obj.confirmed_on,
            "user_defined": comp_obj.status == "user-defined",
            "lines": [
                {"code": ln.code, "share": ln.share, "label": ln.label}
                for ln in comp_obj.lines
            ],
        },
    )
    Run.objects.filter(run_id=res.run_id).delete()
    run = Run.objects.create(
        run_id=res.run_id,
        created=datetime.fromisoformat(m["created"]),
        params=m["params"],
        manifest=m,
        provisional=m["provisional"],
        user_defined=comp.user_defined,
        composition=comp,
        seconds=seconds,
    )
    for s in m["sources"]:
        ed, _ = DataEdition.objects.get_or_create(
            file=s["file"], sha256=s["sha256"], role=s["role"]
        )
        run.editions.add(ed)
    RunInput.objects.bulk_create(
        RunInput(run=run, name=k, value=json.dumps(v)) for k, v in m["params"].items()
    )
    rows = []
    for name, df in tables.items():
        for i, rec in enumerate(_rows(df)):
            rows.append(
                ResultRow(
                    run=run,
                    table=name,
                    position=i,
                    country=str(rec.get("country") or rec.get("economy") or "")[:8],
                    industry=str(rec.get("industry") or "")[:16],
                    data=rec,
                )
            )
    ResultRow.objects.bulk_create(rows, batch_size=2000)
    _store_cdm(res, run)
    return run


def _store_cdm(res, run: Run) -> None:
    try:
        out = cdm.write(res)
    except FileNotFoundError:
        return  # FIGARO description workbook not on this machine
    for name, df in out.items():
        model = MODELS[name]
        pk = model._meta.pk.name
        for rec in _rows(df):
            model.objects.update_or_create(**{pk: rec.pop(pk)}, defaults=rec)
    lines = res.tables["lines"]
    constraints = out["RealResourceConstraint"]
    ext = []
    for cid, r in zip(constraints["constraint_id"], lines.itertuples(), strict=True):
        ext.append(
            RequirementExtension(
                constraint_id=cid,
                run=run,
                required_quantity=_clean(r.extra_persons_all),
                assessment_category=r.rating,
                availability_basis=(
                    None
                    if r.rating == NO_RATING
                    else f"survey proxy: {res.params.slack_indicator}"
                ),
            )
        )
    RequirementExtension.objects.filter(run=run).delete()
    RequirementExtension.objects.bulk_create(ext)


def import_saved(run_id: str) -> Run:
    """Load a run saved by the command line into the database."""
    res = pipeline.load(run_id)
    return store(res, engine_tables(res))


def engine_tables(res) -> dict:
    """Every table the pages show, each produced by an engine function."""
    tables = dict(res.tables)
    tables["country_lines"] = results.lines_table(res)
    tables["dependencies"] = results.dependencies_table(res)
    tables["overview"] = results.overview(res)
    if SWEDEN in res.params.countries:
        tables.update(sweden.run(res))
    return tables
