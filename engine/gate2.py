"""Gate 2 evidence: the engine end to end on the 2026 edition for all 27 states.

``python -m engine gate2 [--provisional]`` runs the standard shock, writes
requirement, availability and rating tables to ``docs/gate-2/`` (requirement
and availability kept separate), runs the edition comparison if a previous
edition is held, and otherwise a same-edition reference-year comparison that
is labelled as a substitute, not the edition test.
"""

from __future__ import annotations

import json

import pandas as pd

from engine import pipeline, robustness
from engine.params import RunParams
from engine.sources._common import REPO_ROOT

OUT_DIR = REPO_ROOT / "docs" / "gate-2"
FOCUS = ("F", "M71", "C28")


def _line(lines: pd.DataFrame, c: str, i: str) -> pd.Series:
    return lines[(lines["economy"] == c) & (lines["industry"] == i)].iloc[0]


def requirement(res) -> pd.DataFrame:
    c = res.tables["countries"].copy()
    lines = res.tables["lines"]
    c["output_multiplier"] = c["required_output_meur"] / c["shock_meur"]
    c["extra_persons_per_meur"] = c["extra_persons_eu"] / c["shock_meur"]
    for i in FOCUS:
        c[f"pressure_{i}"] = [_line(lines, k, i)["pressure"] for k in c["country"]]
    keep = ["country", "shock_meur", "required_output_meur", "output_multiplier",
            "required_home_share", "required_rest_eu_share", "required_non_eu_share",
            "extra_persons_eu", "extra_hours_eu", "extra_persons_per_meur",
            *[f"pressure_{i}" for i in FOCUS]]  # fmt: skip
    return c[keep]


def availability(res) -> pd.DataFrame:
    lines = res.tables["lines"]
    rows = []
    for c in res.params.countries:
        own = lines[lines["economy"] == c]
        counts = own["slack_class"].fillna("none").value_counts()
        row = {"country": c}
        for k in ("high", "elevated", "low", "none"):
            row[f"industries_slack_{k}"] = int(counts.get(k, 0))
        for i in FOCUS:
            ln = _line(lines, c, i)
            row[f"slack_{i}_class"] = (
                ln["slack_class"] if pd.notna(ln["slack_class"]) else "none"
            )
            row[f"slack_{i}_percentile"] = ln["slack_percentile"]
        f = _line(lines, c, "F")
        row["slack_F_current_share_of_firms"] = f["slack_current"]
        row["slack_F_years"] = f["slack_years"]
        row["slack_F_last_quarter"] = f["slack_last"]
        rows.append(row)
    return pd.DataFrame(rows)


def ratings(res) -> pd.DataFrame:
    lines = res.tables["lines"]
    c = res.tables["countries"].set_index("country")
    rows = []
    for k in res.params.countries:
        own = lines[lines["economy"] == k]["rating"].value_counts()
        rows.append(
            {
                "country": k,
                "industries_binding": int(own.get("binding", 0)),
                "industries_tight": int(own.get("tight", 0)),
                "industries_clear": int(own.get("clear", 0)),
                "industries_no_rating": int(own.get("no rating", 0)),
                "rating_F": _line(lines, k, "F")["rating"],
                "rating_M71": _line(lines, k, "M71")["rating"],
                "rating_C28": _line(lines, k, "C28")["rating"],
                "headline_tight_or_binding_share": c.at[
                    k, "headline_tight_or_binding_share"
                ],
                "unrated_share": c.at[k, "unrated_share"],
                "data_quality": c.at[k, "data_quality"],
                "data_quality_flags": c.at[k, "data_quality_flags"],
            }
        )
    return pd.DataFrame(rows)


def run(allow_unconfirmed: bool = False) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_params = RunParams()
    base = pipeline.run(base_params, allow_unconfirmed)
    pipeline.save(base)
    tables = {
        "requirement_by_country.csv": requirement(base),
        "availability_by_country.csv": availability(base),
        "ratings_by_country.csv": ratings(base),
    }
    runs = [base.manifest]

    previous = str(int(base_params.edition) - 1)
    try:
        prev = pipeline.run(
            RunParams(edition=previous, ref_year=base_params.ref_year - 1),
            allow_unconfirmed,
        )
        same_year = pipeline.run(
            RunParams(ref_year=base_params.ref_year - 1), allow_unconfirmed
        )
        edition = robustness.edition_test(same_year.tables["lines"],
                                          prev.tables["lines"])  # fmt: skip
        edition["status"] = "run"
        runs += [prev.manifest, same_year.manifest]
    except FileNotFoundError:
        edition = {
            "status": "not run",
            "reason": f"FIGARO {previous} edition not held; requested from Eurostat",
        }

    alt_year = pipeline.run(
        RunParams(ref_year=base_params.ref_year - 1), allow_unconfirmed
    )
    pipeline.save(alt_year)
    runs.append(alt_year.manifest)
    year_test = robustness.compare_ratings(base.tables["lines"],
                                           alt_year.tables["lines"])  # fmt: skip
    year_test["note"] = (
        "Same edition, reference year 2023 against 2024. Slack is identical in "
        "both runs, so only the requirement side varies. This is not the "
        "edition test and does not apply the stopping rule."
    )

    for name, df in tables.items():
        df.to_csv(OUT_DIR / name, index=False, lineterminator="\n")
    summary = {
        "provisional": any(m["provisional"] for m in runs),
        "base_run": base.run_id,
        "edition_test": edition,
        "reference_year_comparison": {"run": alt_year.run_id, **year_test},
        "runs": [
            {"run_id": m["run_id"], "params": m["params"],
             "composition": m["composition"], "provisional": m["provisional"],
             "sources": m["sources"]}
            for m in runs
        ],
    }  # fmt: skip
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=1),
                                          encoding="utf-8")  # fmt: skip
    return summary
