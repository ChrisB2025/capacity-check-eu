"""Phase 3. The full run matrix and the EU-wide results tables.

``python -m engine results [--provisional]`` runs every combination of shock
size, composition, thresholds and slack indicator on each FIGARO edition held,
saves each run to ``data/processed/runs/<run_id>/``, and writes to
``docs/results/``:

``countries.csv``     per country: headline, requirement total, data quality
``lines.csv``         per country and industry: requirement with its home,
                      rest-of-EU and non-EU split, pressure, slack, rating
``dependencies.csv``  required output in the insulation, heat pump, building
                      materials and related manufacturing industries, by
                      country, with no rating
``robustness.csv``    ratings changed against the base run, by test
``plausibility.csv``  France and Ireland against official job estimates
``sweden_*.csv``      the Sweden layer for the base run (Phase 5)
``matrix.csv``        every run in the matrix with its parameters and results
``overview.csv``      the EU totals and one worked example shown on the
                      web app's front page
``summary.json``      run ids, sources and checksums

The base run is the default parameters. Tables other than ``matrix.csv`` and
``robustness.csv`` describe the base run.
"""

from __future__ import annotations

import itertools
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from engine import pipeline, plausibility, rating, robustness, sweden
from engine.params import RunParams, Thresholds
from engine.sources._common import REPO_ROOT

OUT_DIR = REPO_ROOT / "docs" / "results"
REVIEW_DIR = REPO_ROOT / "docs" / "review"
REVIEW_DOCS = ("method-note.md", "composition-table.md", "gate-3-report.md",
               "cdm-mapping.md", "data-register.md")  # fmt: skip

SHOCKS = (0.5, 1.0, 2.0)
COMPOSITIONS = ("standard", "alt_contractor", "alt_materials", "alt_heating")
THRESHOLDS = {
    "default": Thresholds(),
    "lower": Thresholds(pressure_low=0.01, pressure_high=0.03),
    "higher": Thresholds(pressure_low=0.03, pressure_high=0.08),
}
SLACK = ("ecfin", "vacancy")
EDITIONS = (("2026", 2024), ("2025", 2023))

# Optional six-group aggregation of the 64 industries. Proposed, published
# with the composition table; not part of any rating.
SIX_GROUPS = {
    "extraction": ("A01", "A02", "A03", "B"),
    "energy": ("D35",),
    "recycling": ("E37-39",),
    "distribution": ("E36", "G45", "G46", "G47", "H49", "H50", "H51", "H52", "H53"),
}


def six_group(code: str) -> str:
    for group, codes in SIX_GROUPS.items():
        if code in codes:
            return group
    if code.startswith("C") or code == "F":
        return "production"
    return "use"


# Dependencies table: manufacturing industries the programme leans on.
DEPENDENCIES = {
    "C16": "building materials",
    "C22": "insulation",
    "C23": "insulation and building materials",
    "C24": "building materials",
    "C25": "building materials",
    "C27": "related manufacturing",
    "C28": "heat pumps and heating equipment",
}


def _variant(name: str, **kw) -> tuple[str, RunParams]:
    return name, RunParams(**kw)


def matrix() -> list[tuple[str, RunParams]]:
    """Every combination, base first. Names describe the departure from base."""
    runs = []
    for (ed, year), shock, comp, (tname, t), sl in itertools.product(
        EDITIONS, SHOCKS, COMPOSITIONS, THRESHOLDS.items(), SLACK
    ):
        parts = [
            f"edition {ed}" if ed != "2026" else "",
            f"shock {shock:g}%" if shock != 1.0 else "",
            comp if comp != "standard" else "",
            f"thresholds {tname}" if tname != "default" else "",
            "vacancy slack" if sl != "ecfin" else "",
        ]
        name = ", ".join(p for p in parts if p) or "base"
        runs.append(
            _variant(
                name,
                edition=ed,
                ref_year=year,
                shock_pct=shock,
                composition=comp,
                thresholds=t,
                slack_indicator=sl,
            )
        )
    runs.sort(key=lambda r: r[0] != "base")
    return runs


def lines_table(res) -> pd.DataFrame:
    """Per shocking country and industry: requirement, then availability."""
    detail = res.tables["industry_detail"]
    lines = res.tables["lines"].rename(columns={"economy": "country"})
    keep = ["country", "industry", "label", "persons_employment",
            "extra_persons_all", "extra_persons_own", "pressure",
            "slack_class", "slack_percentile", "slack_current", "slack_years",
            "rating"]  # fmt: skip
    out = detail.merge(lines[keep], on=["country", "industry"], how="left")
    out["required_total_meur"] = out[
        ["required_home_meur", "required_rest_eu_meur", "required_non_eu_meur"]
    ].sum(axis=1)
    out["six_group"] = out["industry"].map(six_group)
    out["slack_class"] = out["slack_class"].fillna("none")
    cols = ["country", "industry", "label", "six_group", "required_total_meur",
            "required_home_meur", "required_rest_eu_meur", "required_non_eu_meur",
            "persons_employment", "extra_persons_all", "extra_persons_own",
            "pressure", "slack_class", "slack_percentile", "slack_current",
            "slack_years", "rating"]  # fmt: skip
    return out[cols]


def dependencies_table(res) -> pd.DataFrame:
    d = res.tables["industry_detail"]
    d = d[d["industry"].isin(DEPENDENCIES)].copy()
    d["role"] = d["industry"].map(DEPENDENCIES)
    d["required_total_meur"] = d[
        ["required_home_meur", "required_rest_eu_meur", "required_non_eu_meur"]
    ].sum(axis=1)
    for k in ("home", "rest_eu", "non_eu"):
        d[f"{k}_share"] = np.where(
            d["required_total_meur"] > 0,
            d[f"required_{k}_meur"] / d["required_total_meur"],
            np.nan,
        )
    lab = res.tables["lines"].drop_duplicates("industry").set_index("industry")
    d["label"] = d["industry"].map(lab["label"])
    return d[["country", "industry", "label", "role", "required_total_meur",
              "required_home_meur", "required_rest_eu_meur",
              "required_non_eu_meur", "home_share", "rest_eu_share",
              "non_eu_share"]]  # fmt: skip


EXAMPLE_COUNTRY = "DE"
EXAMPLE_INDUSTRY = "F"


def overview(res) -> pd.DataFrame:
    """One row: EU totals and a worked example, for the front page.

    The example is construction in Germany, or in the country with the largest
    shock when Germany is not in the run.
    """
    c = res.tables["countries"]
    lines = res.tables["lines"]
    out = c["required_output_meur"]
    jobs = c["extra_persons_eu"]
    head = c["headline_tight_or_binding_share"]
    counts = lines["rating"].value_counts()
    ex = (
        EXAMPLE_COUNTRY
        if EXAMPLE_COUNTRY in set(c["country"])
        else c.loc[c["shock_meur"].idxmax(), "country"]
    )
    exc = c.set_index("country").loc[ex]
    exl = lines[(lines["economy"] == ex) & (lines["industry"] == EXAMPLE_INDUSTRY)]
    exl = exl.iloc[0]
    rated = head.notna()
    row = {
        "shock_pct": res.params.shock_pct,
        "gdp_year": res.params.gdp_year,
        "countries": len(c),
        "shock_meur": c["shock_meur"].sum(),
        "required_output_meur": out.sum(),
        **{
            f"required_{k}_share": (out * c[f"required_{k}_share"]).sum() / out.sum()
            for k in ("home", "rest_eu", "non_eu")
        },
        "extra_persons_eu": jobs.sum(),
        "headline_jobs_weighted": (head[rated] * jobs[rated]).sum() / jobs[rated].sum(),
        "headline_min": head.min(),
        "headline_min_country": c.loc[head.idxmin(), "country"],
        "headline_max": head.max(),
        "headline_max_country": c.loc[head.idxmax(), "country"],
        "unrated_jobs_weighted": (c["unrated_share"] * jobs).sum() / jobs.sum(),
        **{
            f"lines_{k.replace(' ', '_')}": int(counts.get(k, 0))
            for k in (rating.BINDING, rating.TIGHT, rating.CLEAR, rating.NO_RATING)
        },
        "example_country": ex,
        "example_shock_meur": exc["shock_meur"],
        "example_extra_persons_eu": exc["extra_persons_eu"],
        "example_headline": exc["headline_tight_or_binding_share"],
        "example_industry": EXAMPLE_INDUSTRY,
        "example_industry_label": exl["label"],
        "example_extra_persons": exl["extra_persons_all"],
        "example_employment": exl["persons_employment"],
        "example_pressure": exl["pressure"],
        "example_slack_current": exl["slack_current"],
        "example_slack_percentile": exl["slack_percentile"],
        "example_slack_class": exl["slack_class"],
        "example_slack_years": exl["slack_years"],
        "example_rating": exl["rating"],
    }
    return pd.DataFrame([row])


def _summary_row(name: str, res) -> dict:
    c = res.tables["countries"]
    lines = res.tables["lines"]
    p = res.params
    counts = lines["rating"].value_counts()
    return {
        "variant": name,
        "run_id": res.run_id,
        "provisional": res.manifest["provisional"],
        "edition": p.edition,
        "ref_year": p.ref_year,
        "shock_pct": p.shock_pct,
        "composition": p.composition,
        "pressure_low": p.thresholds.pressure_low,
        "pressure_high": p.thresholds.pressure_high,
        "slack_indicator": p.slack_indicator,
        "extra_persons_eu": c["extra_persons_eu"].sum(),
        "headline_min": c["headline_tight_or_binding_share"].min(),
        "headline_median": c["headline_tight_or_binding_share"].median(),
        "headline_max": c["headline_tight_or_binding_share"].max(),
        **{
            f"lines_{k.replace(' ', '_')}": int(counts.get(k, 0))
            for k in (rating.BINDING, rating.TIGHT, rating.CLEAR, rating.NO_RATING)
        },
    }


def _test_of(name: str) -> str:
    if name.startswith("edition"):
        return "edition"
    if "," in name:
        return "combined"
    if name.startswith("shock"):
        return "shock size"
    if name.startswith("alt_"):
        return "composition"
    if name.startswith("thresholds"):
        return "thresholds"
    if name == "vacancy slack":
        return "slack indicator"
    return "base"


def run(allow_unconfirmed: bool = False, progress=print) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plan = matrix()
    results, skipped = {}, []
    for name, params in plan:
        try:
            res = pipeline.run(params, allow_unconfirmed)
        except FileNotFoundError:
            skipped.append({"variant": name, "reason": "data not held"})
            continue
        pipeline.save(res)
        results[name] = res
        progress(f"{res.run_id}  {name}")

    base = results["base"]
    rows, robust = [], []
    for name, res in results.items():
        rows.append(_summary_row(name, res))
        if name == "base":
            continue
        cmp = robustness.compare_ratings(base.tables["lines"], res.tables["lines"])
        robust.append(
            {
                "test": _test_of(name),
                "variant": name,
                "run_id": res.run_id,
                **{k: v for k, v in cmp.items() if k != "transitions"},
                "transitions": "; ".join(
                    f"{t['rating_base']} to {t['rating_alt']}: {t['lines']}"
                    for t in cmp["transitions"]
                ),
            }
        )
    edition_held = any(n.startswith("edition") for n in results)
    tables = {
        "countries.csv": base.tables["countries"],
        "lines.csv": lines_table(base),
        "dependencies.csv": dependencies_table(base),
        "robustness.csv": pd.DataFrame(robust),
        "matrix.csv": pd.DataFrame(rows),
        "plausibility.csv": pd.DataFrame(plausibility.run(base)),
        "overview.csv": overview(base),
    }
    for name, df in sweden.run(base).items():
        if "publishable" in df.columns:
            # Konjunkturinstitutet rows wait for its reuse licence (gate 1).
            df = df[df["publishable"]].drop(columns="publishable")
        tables[f"{name}.csv"] = df
    for fname, df in tables.items():
        df.to_csv(OUT_DIR / fname, index=False, lineterminator="\n")
    summary = {
        "provisional": any(r.manifest["provisional"] for r in results.values()),
        "base_run": base.run_id,
        "runs": len(results),
        "skipped": skipped,
        "edition_test": "run" if edition_held else "not run: FIGARO 2025 not held",
        "sources": base.manifest["sources"],
        "base_params": base.manifest["params"],
        "composition": base.manifest["composition"],
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=1), encoding="utf-8"
    )
    review_package(summary["provisional"])
    return summary


def review_package(provisional: bool) -> Path:
    """Method note, composition table, results and robustness, as one zip."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    name = "review-package-provisional.zip" if provisional else "review-package.zip"
    out = REVIEW_DIR / name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for doc in REVIEW_DOCS:
            z.write(REPO_ROOT / "docs" / doc, f"docs/{doc}")
        for f in sorted(OUT_DIR.iterdir()):
            z.write(f, f"results/{f.name}")
    return out
