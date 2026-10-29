"""A full run: shock, supply chains, jobs, pressure, slack, rating, headline.

``run(params)`` returns the result tables; ``save(result)`` writes them with a
manifest to ``data/processed/runs/<run_id>/``. The run id is derived from the
parameters, the composition file and the checksums of every data file read,
so the same inputs always give the same id.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from engine import __version__, concordance, io_model, jobs, rating, shock, slack
from engine.params import RunParams
from engine.sources._common import EU27, PROCESSED_DIR, read_provenance, utc_now

RUNS_DIR = PROCESSED_DIR / "runs"
SHORT_HISTORY_YEARS = 10.0


@dataclass
class Result:
    run_id: str
    params: RunParams
    manifest: dict
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)


def _sources(model, composition_path: Path) -> list[dict]:
    files = [
        PROCESSED_DIR / "nama_10_gdp.parquet",
        PROCESSED_DIR / "nama_10_a64_e.parquet",
        PROCESSED_DIR / "jvs_q_nace2.parquet",
        sorted(PROCESSED_DIR.glob("ecfin_bcs_rel*.parquet"))[-1],
    ]
    out = [
        {
            "file": model.source_file,
            "sha256": model.source_sha256,
            "role": "FIGARO table",
        }
    ]
    for f in files:
        for s in read_provenance(f).get("sources", []):
            out.append({"file": s["file"], "sha256": s["sha256"], "role": f.stem})
    out.append(
        {
            "file": composition_path.name,
            "sha256": hashlib.sha256(composition_path.read_bytes()).hexdigest(),
            "role": "composition",
        }
    )
    return out


def run(params: RunParams, allow_unconfirmed: bool = False) -> Result:
    comp = shock.load_composition(params.composition)
    if not allow_unconfirmed:
        comp.require_confirmed()
    comp_path = shock.composition_path(params.composition)

    M = io_model.model(params.edition, params.ref_year)
    gdp = shock.gdp_meur(params.gdp_year, params.countries)
    a64 = concordance.load().set_index("figaro_code")
    eu = set(EU27)

    # Steps 1 and 2: direct demand and required output, per shocking country.
    direct, required = [], {}
    for c in params.countries:
        dd = shock.direct_demand(
            M, comp, c, gdp[c], params.shock_pct, params.import_basis
        )
        direct.append(dd.by_product.assign(country=c, shock_meur=dd.amount_meur))
        required[c] = M.L @ dd.y

    # Step 3: jobs on EU lines.
    coefs = jobs.coefficients(M, EU27)
    pos = np.array(
        [
            M.position(e, i)
            for e, i in zip(coefs["economy"], coefs["industry"], strict=True)
        ]
    )
    persons_per = coefs["persons_per_meur"].to_numpy()
    hours_per = coefs["hours_per_meur"].to_numpy()

    # Industry detail: for each shocking country and industry, where the
    # required output sits (home, rest of EU, outside EU) and its jobs.
    econ_of = np.repeat(np.array(M.economies), len(M.industries))
    ind_of = np.tile(np.array(M.industries), len(M.economies))
    detail_rows = []
    for c, req in required.items():
        for i in M.industries:
            mask = ind_of == i
            home = req[mask & (econ_of == c)].sum()
            rest = req[mask & np.isin(econ_of, list(eu - {c}))].sum()
            non = req[mask & ~np.isin(econ_of, list(eu))].sum()
            detail_rows.append(
                {
                    "country": c,
                    "industry": i,
                    "required_home_meur": home,
                    "required_rest_eu_meur": rest,
                    "required_non_eu_meur": non,
                }
            )
    detail = pd.DataFrame(detail_rows)

    # Extra persons on each EU line from each shocking country.
    jobs_from = pd.DataFrame(
        {c: required[c][pos] * persons_per for c in params.countries}
    )
    hours_from = pd.DataFrame(
        {c: required[c][pos] * hours_per for c in params.countries}
    )

    # Step 4: pressure on each EU line.
    lines = coefs[
        [
            "economy",
            "industry",
            "persons_employment",
            "hours_employment",
            "persons_basis",
            "hours_basis",
            "persons_publisher_flag",
            "output_meur",
        ]
    ].copy()
    lines["required_meur_all"] = sum(required[c][pos] for c in params.countries)
    lines["extra_persons_all"] = jobs_from.sum(axis=1).to_numpy()
    lines["extra_hours_all"] = hours_from.sum(axis=1).to_numpy()
    own = np.array(
        [
            jobs_from.at[k, e] if e in jobs_from.columns else 0.0
            for k, e in enumerate(lines["economy"])
        ]
    )
    lines["extra_persons_own"] = own
    basis = lines["extra_persons_all"] if params.application == "simultaneous" else own
    with np.errstate(divide="ignore", invalid="ignore"):
        lines["pressure"] = np.where(
            lines["persons_employment"] > 0,
            basis / lines["persons_employment"],
            np.nan,
        )

    # Steps 5 and 6: slack and rating.
    sl = slack.slack(params)
    lines = lines.merge(sl, on=["economy", "industry"], how="left")
    lines["rating"] = rating.rate_lines(lines, params.thresholds)
    lines.loc[lines["persons_basis"] == jobs.BASIS_MISSING, "rating"] = rating.NO_RATING
    lines["label"] = lines["industry"].map(a64["label"])

    # Step 7: headline and data quality, per shocking country.
    rating_of = lines["rating"].to_numpy()
    imputed = (lines["persons_basis"] == jobs.BASIS_SECTION).to_numpy()
    country_rows = []
    for c in params.countries:
        j = np.nan_to_num(jobs_from[c].to_numpy())
        total = j.sum()
        req = required[c]
        req_total = req.sum()
        tight = j[np.isin(rating_of, [rating.TIGHT, rating.BINDING])].sum()
        unrated = j[rating_of == rating.NO_RATING].sum()
        notes = []
        f_line = lines[(lines["economy"] == c) & (lines["industry"] == "F")].iloc[0]
        if f_line["slack_class"] is None or pd.isna(f_line["slack_class"]):
            notes.append("construction slack unavailable")
        elif f_line["slack_years"] < SHORT_HISTORY_YEARS:
            notes.append(
                f"construction slack history {f_line['slack_years']:.0f} years"
            )
        grade, flags = rating.quality(
            {
                "jobs on unrated lines": unrated / total if total else 0.0,
                "jobs on section-ratio lines": (
                    j[imputed].sum() / total if total else 0.0
                ),
            },
            notes,
        )
        country_rows.append(
            {
                "country": c,
                "shock_meur": params.shock_pct / 100 * gdp[c],
                "required_output_meur": req_total,
                "required_home_share": req[econ_of == c].sum() / req_total,
                "required_rest_eu_share": req[np.isin(econ_of, list(eu - {c}))].sum()
                / req_total,
                "required_non_eu_share": req[~np.isin(econ_of, list(eu))].sum()
                / req_total,
                "extra_persons_eu": total,
                "extra_hours_eu": np.nansum(hours_from[c].to_numpy()),
                "headline_tight_or_binding_share": tight / total if total else np.nan,
                "unrated_share": unrated / total if total else np.nan,
                "data_quality": grade,
                "data_quality_flags": flags,
            }
        )
    countries = pd.DataFrame(country_rows)

    sources = _sources(M, comp_path)
    digest = hashlib.sha256(
        json.dumps(
            {"params": params.as_dict(), "sources": sources}, sort_keys=True
        ).encode()
    ).hexdigest()
    run_id = digest[:12]
    manifest = {
        "run_id": run_id,
        "engine_version": __version__,
        "created": utc_now().isoformat(),
        "params": params.as_dict(),
        "composition": {
            "name": comp.name,
            "status": comp.status,
            "confirmed_by": comp.confirmed_by,
            "confirmed_on": comp.confirmed_on,
        },
        "sources": sources,
        # A provisional run uses a composition not yet confirmed after review.
        # Its figures are for internal checking and must not be published.
        "provisional": comp.status != "confirmed",
    }
    tables = {
        "countries": countries,
        "lines": lines,
        "industry_detail": detail,
        "direct_demand": pd.concat(direct, ignore_index=True),
    }
    return Result(run_id, params, manifest, tables)


def save(result: Result) -> Path:
    out = RUNS_DIR / result.run_id
    out.mkdir(parents=True, exist_ok=True)
    for name, df in result.tables.items():
        df.to_csv(out / f"{name}.csv", index=False, lineterminator="\n")
    (out / "manifest.json").write_text(
        json.dumps(result.manifest, indent=1), encoding="utf-8"
    )
    return out
