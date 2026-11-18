"""How much the estimated risk categories rest on the thresholds.

Two parts:

``table(res)``
    For one run, the ratings under other pressure thresholds and other slack
    cut-offs. The pressure variants are exact without rerunning the model:
    pressure and the slack class do not depend on the pressure thresholds,
    so the stored lines are re-rated with ``rating.rate``. The slack variants
    rerun only step 5 (``slack.slack``) with the other cut-offs, then re-rate.
    Each row gives the counts by category, the lines that change against the
    run, and the EU-wide share of the shock's jobs on tight or binding lines.

``employment_reference()``
    An empirical reference point for the pressure thresholds: how often an
    industry's employment in one member state has grown by at least the
    threshold in a single year, from the national accounts series already
    held (``nama_10_a64_e``). Written to ``docs/results/threshold_reference.csv``
    by ``python -m engine glossary``.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from engine import concordance, jobs, rating, robustness, slack
from engine.params import Thresholds
from engine.sources._common import PROCESSED_DIR, REPO_ROOT

PRESSURE_LOW = (0.01, 0.02, 0.03)
PRESSURE_HIGH = (0.03, 0.05, 0.08)
SLACK_MEDIAN = (0.5, 0.6)
SLACK_TOP = (0.67, 0.75, 0.8)

SLACK_COLUMNS = ("slack_indicator", "slack_current", "slack_percentile",
                 "slack_median", "slack_top_quartile", "slack_years",
                 "slack_first", "slack_last", "slack_class", "slack_note",
                 "slack_source")  # fmt: skip

REFERENCE_FILE = REPO_ROOT / "docs" / "results" / "threshold_reference.csv"
REFERENCE_CUTOFFS = (0.01, 0.02, 0.03, 0.05, 0.08)
REFERENCE_FIRST_YEAR = 2011  # first year with a change from 2010
REFERENCE_LAST_YEAR = 2024  # the FIGARO reference year; later years are estimates


def rerate(lines: pd.DataFrame, t: Thresholds) -> pd.Series:
    """Ratings for ``lines`` under thresholds ``t``, as ``pipeline.run`` sets them."""
    out = rating.rate_lines(lines, t)
    if "persons_basis" in lines.columns:
        out[lines["persons_basis"] == jobs.BASIS_MISSING] = rating.NO_RATING
    return out


def _jobs_share(lines: pd.DataFrame, ratings: pd.Series) -> float:
    """EU-wide share of the shock's jobs on tight or binding lines.

    Equal to the jobs-weighted mean of the member states' headlines, because
    each line's extra persons are the sum over every programme in the run.
    """
    j = lines["extra_persons_all"].fillna(0).to_numpy()
    total = j.sum()
    if not total:
        return float("nan")
    hit = ratings.isin([rating.TIGHT, rating.BINDING]).to_numpy()
    return float(j[hit].sum() / total)


def _row(kind, t: Thresholds, current: Thresholds, lines, ratings) -> dict:
    alt = lines[["economy", "industry"]].assign(rating=ratings.to_numpy())
    cmp = robustness.compare_ratings(lines, alt)
    counts = ratings.value_counts()
    return {
        "kind": kind,
        "pressure_low": t.pressure_low,
        "pressure_high": t.pressure_high,
        "slack_median_quantile": t.slack_median_quantile,
        "slack_top_quantile": t.slack_top_quantile,
        "current": t == current,
        **{
            f"lines_{k.replace(' ', '_')}": int(counts.get(k, 0))
            for k in (rating.BINDING, rating.TIGHT, rating.CLEAR, rating.NO_RATING)
        },
        "ratings_changed": cmp["ratings_changed"],
        "share_changed": cmp["share_changed"],
        "transitions": "; ".join(
            f"{x['rating_base']} to {x['rating_alt']}: {x['lines']}"
            for x in cmp["transitions"]
        ),
        "jobs_tight_or_binding_share": _jobs_share(lines, ratings),
    }


def pressure_variants(current: Thresholds) -> list[Thresholds]:
    out = [
        replace(current, pressure_low=lo, pressure_high=hi)
        for lo in PRESSURE_LOW
        for hi in PRESSURE_HIGH
        if lo < hi
    ]
    return out if current in out else [current, *out]


def slack_variants(current: Thresholds) -> list[Thresholds]:
    out = [
        replace(current, slack_median_quantile=m, slack_top_quantile=q)
        for m in SLACK_MEDIAN
        for q in SLACK_TOP
        if m < q
    ]
    return out if current in out else [current, *out]


def pressure_grid(lines: pd.DataFrame, current: Thresholds) -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row("pressure", t, current, lines, rerate(lines, t))
            for t in pressure_variants(current)
        ]
    )


_SLACK_CACHE: dict[tuple, pd.DataFrame] = {}


def _slack(params) -> pd.DataFrame:
    """``slack.slack`` for these parameters, cached on the ones it reads.

    The slack step does not depend on the shock, composition or edition, so
    importing many runs computes each set of cut-offs once.
    """
    t = params.thresholds
    key = (params.slack_indicator, params.slack_seasonally_adjusted,
           params.slack_window_quarters, params.slack_min_years,
           tuple(params.countries), t.slack_median_quantile,
           t.slack_top_quantile)  # fmt: skip
    if key not in _SLACK_CACHE:
        _SLACK_CACHE[key] = slack.slack(params)
    return _SLACK_CACHE[key]


def slack_grid(lines: pd.DataFrame, params) -> pd.DataFrame:
    current = params.thresholds
    base = lines.drop(columns=[c for c in SLACK_COLUMNS if c in lines.columns])
    rows = []
    for t in slack_variants(current):
        if t == current:
            relined = lines
        else:
            sl = _slack(replace(params, thresholds=t))
            relined = base.merge(sl, on=["economy", "industry"], how="left")
        rows.append(_row("slack", t, current, lines, rerate(relined, t)))
    return pd.DataFrame(rows)


def table(res) -> pd.DataFrame:
    """Both grids for one run, pressure first."""
    lines = res.tables["lines"]
    return pd.concat(
        [
            pressure_grid(lines, res.params.thresholds),
            slack_grid(lines, res.params),
        ],
        ignore_index=True,
    )


def employment_reference() -> pd.DataFrame:
    """How often one industry in one member state grew by each cut-off in a year.

    Persons employed (``EMP_DC``, ``THS_PER``) for the 64 industries, year on
    year, from 2011 to the reference year. ``share_of_years`` counts each
    country, industry and year once; ``share_weighted`` weights by the
    industry's employment in the earlier year, so small industries count less.
    """
    df = pd.read_parquet(PROCESSED_DIR / "nama_10_a64_e.parquet")
    codes = set(concordance.load()["nama_code"])
    df = df[
        (df["unit"] == "THS_PER")
        & (df["na_item"] == "EMP_DC")
        & df["nace_r2"].isin(codes)
        & (df["year"] <= REFERENCE_LAST_YEAR)
    ]
    p = df.pivot_table(index=["geo", "nace_r2"], columns="year", values="obs_value")
    prev = p.shift(1, axis=1)
    growth = (p / prev - 1).loc[:, REFERENCE_FIRST_YEAR:]
    weight = prev.loc[:, REFERENCE_FIRST_YEAR:]
    long = (
        pd.DataFrame({"growth": growth.stack(), "weight": weight.stack()})
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    rows = []
    for scope, sel in (
        ("all industries", long),
        ("construction (F)", long.xs("F", level="nace_r2", drop_level=False)),
    ):
        for cut in REFERENCE_CUTOFFS:
            hit = sel["growth"] >= cut
            rows.append(
                {
                    "scope": scope,
                    "cutoff": cut,
                    "share_of_years": float(hit.mean()),
                    "share_weighted": float(
                        sel.loc[hit, "weight"].sum() / sel["weight"].sum()
                    ),
                    "median_growth": float(sel["growth"].median()),
                    "observations": int(len(sel)),
                    "first_year": REFERENCE_FIRST_YEAR,
                    "last_year": REFERENCE_LAST_YEAR,
                }
            )
    return pd.DataFrame(rows)


def write_reference() -> str:
    REFERENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    employment_reference().to_csv(REFERENCE_FILE, index=False, lineterminator="\n")
    return str(REFERENCE_FILE)


def load_reference() -> pd.DataFrame | None:
    """The committed reference table, or None before it has been written."""
    if not REFERENCE_FILE.exists():
        return None
    return pd.read_csv(REFERENCE_FILE)
