"""The fixed test set: a handful of runs whose outputs are stored as fixtures.

Any later change to the engine (or, from Phase 6, to a prompt) is checked by
rerunning these cases and comparing with the stored outputs.
``python -m engine testset`` regenerates the fixtures; regenerate only when a
change in results is intended, and say why in the commit.

The fixtures record the composition's status. Fixtures generated from a
composition that has not been confirmed are provisional and are regenerated
once it is.
"""

from __future__ import annotations

import json

import pandas as pd

from engine import pipeline
from engine.params import RunParams, Thresholds
from engine.sources._common import REPO_ROOT

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "expected"

CASES: dict[str, dict] = {
    "base": {},
    "shock_0_5": {"shock_pct": 0.5},
    "shock_2_0": {"shock_pct": 2.0},
    "reference_year_2023": {"ref_year": 2023},
    "composition_contractor": {"composition": "alt_contractor"},
    "thresholds_test": {
        "thresholds": Thresholds(pressure_low=0.01, pressure_high=0.03)
    },
    "slack_vacancy": {"slack_indicator": "vacancy"},
    "application_own": {"application": "own"},
}

COUNTRY_COLS = [
    "country",
    "shock_meur",
    "required_output_meur",
    "extra_persons_eu",
    "headline_tight_or_binding_share",
    "unrated_share",
    "data_quality",
]
LINE_COLS = ["economy", "industry", "extra_persons_all", "pressure", "slack_class",
             "rating"]  # fmt: skip


def run_case(name: str, allow_unconfirmed: bool = False):
    return pipeline.run(RunParams(**CASES[name]), allow_unconfirmed)


def outputs(res) -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        res.tables["countries"][COUNTRY_COLS].copy(),
        res.tables["lines"][LINE_COLS].copy(),
    )


def generate(allow_unconfirmed: bool = False) -> list[str]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name in CASES:
        res = run_case(name, allow_unconfirmed)
        countries, lines = outputs(res)
        countries.to_csv(FIXTURE_DIR / f"{name}_countries.csv", index=False,
                         lineterminator="\n", float_format="%.12g")  # fmt: skip
        lines.to_csv(FIXTURE_DIR / f"{name}_lines.csv", index=False,
                     lineterminator="\n", float_format="%.12g")  # fmt: skip
        (FIXTURE_DIR / f"{name}_manifest.json").write_text(
            json.dumps(
                {"run_id": res.run_id, "provisional": res.manifest["provisional"],
                 "composition": res.manifest["composition"],
                 "params": res.manifest["params"]},
                indent=1,
            ),
            encoding="utf-8",
        )  # fmt: skip
        written.append(name)
    return written
