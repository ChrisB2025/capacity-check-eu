"""Step 5. Starting slack: shortage indicators against their own history.

For each member state and industry, the indicator's current level (the mean
of the latest ``window`` quarters, or three times as many months) is placed
within the history of the same rolling mean. The output is the percentile of
the current level, the history's median and upper quartile, and a class:

* ``low``: at or below the median of its own history
* ``elevated``: above the median, below the top quartile
* ``high``: in the top quartile

Primary indicator: share of firms naming labour as a factor limiting activity
(DG ECFIN). Industries made of several NACE divisions take the simple mean of
the divisions with data in each period; construction uses the survey's total
for the sector. Alternative indicator: Eurostat job vacancy rate for the
industry's NACE section.

A line gets no slack class, and hence no rating, when the series is missing
or has less history than ``min_years``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine import concordance
from engine.sources import ecfin
from engine.sources._common import EU27, PROCESSED_DIR, read_provenance

LOW, ELEVATED, HIGH = "low", "elevated", "high"


@dataclass(frozen=True)
class Position:
    current: float
    percentile: float
    median: float
    top_quartile: float
    years: float
    first: str
    last: str
    slack_class: str | None
    note: str


def position(
    series: pd.Series,
    window: int,
    min_years: float,
    median_q: float = 0.5,
    top_q: float = 0.75,
    per_year: int = 4,
) -> Position:
    """Place the latest rolling mean of ``series`` in its own history.

    ``series`` is indexed by period in time order, without gaps filled.
    """
    s = series.dropna()
    if s.empty:
        return Position(np.nan, np.nan, np.nan, np.nan, 0.0, "", "", None, "no series")
    years = len(s) / per_year
    rolled = s.rolling(window, min_periods=window).mean().dropna()
    if rolled.empty:
        return Position(
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            years,
            str(s.index[0]),
            str(s.index[-1]),
            None,
            "history shorter than window",
        )
    current = float(rolled.iloc[-1])
    med = float(rolled.quantile(median_q))
    top = float(rolled.quantile(top_q))
    pct = float((rolled <= current).mean())
    if years < min_years:
        cls, note = None, f"history {years:.1f} years, below {min_years:g}"
    elif current >= top:
        cls, note = HIGH, ""
    elif current > med:
        cls, note = ELEVATED, ""
    else:
        cls, note = LOW, ""
    return Position(
        current, pct, med, top, years, str(s.index[0]), str(s.index[-1]), cls, note
    )


def _ecfin_frame(adjusted: bool) -> tuple[pd.DataFrame, str]:
    path = sorted(PROCESSED_DIR.glob("ecfin_bcs_rel*.parquet"))[-1]
    labour = read_provenance(path)["labour_codes"]
    cols = [
        "survey",
        "country",
        "sector",
        "question",
        "answer",
        "freq",
        "period",
        "value",
        "seasonally_adjusted",
    ]
    df = pd.read_parquet(path, columns=cols)
    lab = ecfin.labour_series(df, labour, adjusted=adjusted)
    lab = lab[lab["country"].isin(EU27)].copy()
    for c in ("survey", "country", "sector", "freq"):
        lab[c] = lab[c].astype(str)
    return lab, path.name


def _to_quarterly(g: pd.DataFrame) -> pd.Series:
    """Quarterly series; monthly series are averaged within each quarter."""
    if g["freq"].iloc[0] == "Q":
        idx = pd.PeriodIndex(g["period"].str.replace("Q", "-Q", regex=False), freq="Q")
        return pd.Series(g["value"].to_numpy(), index=idx).sort_index()
    idx = pd.PeriodIndex(g["period"], freq="M").asfreq("Q")
    grouped = pd.Series(g["value"].to_numpy(), index=idx).groupby(level=0)
    means, counts = grouped.mean(), grouped.count()
    return means[counts == 3]  # only quarters with all three months


def ecfin_slack(params) -> pd.DataFrame:
    lab, source = _ecfin_frame(params.slack_seasonally_adjusted)
    series = {
        (r.survey, r.country, r.sector): _to_quarterly(g)
        for r, g in (
            (g.iloc[0], g)
            for _, g in lab.groupby(["survey", "country", "sector"], observed=True)
        )
    }
    a64 = concordance.load()
    t = params.thresholds
    rows = []
    for c in params.countries:
        for r in a64.itertuples():
            note_extra = ""
            if not r.ecfin_survey:
                parts = []
                note_extra = "no survey question for this industry"
            elif r.ecfin_survey == "building" and ("building", c, "TOT") in series:
                parts = [series[("building", c, "TOT")]]
                note_extra = "construction total"
            else:
                parts = [
                    series[(r.ecfin_survey, c, d)]
                    for d in r.ecfin_divisions.split()
                    if (r.ecfin_survey, c, d) in series
                ]
                if parts and len(parts) < len(r.ecfin_divisions.split()):
                    note_extra = (
                        f"{len(parts)} of {len(r.ecfin_divisions.split())} divisions"
                    )
            combined = (
                pd.concat(parts, axis=1).mean(axis=1)
                if parts
                else pd.Series(dtype=float)
            )
            p = position(
                combined,
                params.slack_window_quarters,
                params.slack_min_years,
                t.slack_median_quantile,
                t.slack_top_quantile,
            )
            rows.append(_row(c, r.figaro_code, "ecfin", p, note_extra, source))
    return pd.DataFrame(rows)


def vacancy_slack(params) -> pd.DataFrame:
    path = PROCESSED_DIR / "jvs_q_nace2.parquet"
    df = pd.read_parquet(path)
    adj = "SA" if params.slack_seasonally_adjusted else "NSA"
    df = df[(df["s_adj"] == adj)].dropna(subset=["obs_value"])
    a64 = concordance.load()
    t = params.thresholds
    rows = []
    for c in params.countries:
        dc = df[df["geo"] == c]
        for r in a64.itertuples():
            g = dc[dc["nace_r2"] == r.nace_section]
            if g.empty:
                s = pd.Series(dtype=float)
            else:
                idx = pd.PeriodIndex(g["period"].str.replace("-Q", "-Q"), freq="Q")
                s = pd.Series(g["obs_value"].to_numpy(), index=idx).sort_index()
            p = position(
                s,
                params.slack_window_quarters,
                params.slack_min_years,
                t.slack_median_quantile,
                t.slack_top_quantile,
            )
            rows.append(
                _row(
                    c,
                    r.figaro_code,
                    "vacancy",
                    p,
                    f"NACE section {r.nace_section}",
                    path.name,
                )
            )
    return pd.DataFrame(rows)


def _row(country, code, indicator, p: Position, note, source) -> dict:
    return {
        "economy": country,
        "industry": code,
        "slack_indicator": indicator,
        "slack_current": p.current,
        "slack_percentile": p.percentile,
        "slack_median": p.median,
        "slack_top_quartile": p.top_quartile,
        "slack_years": p.years,
        "slack_first": p.first,
        "slack_last": p.last,
        "slack_class": p.slack_class,
        "slack_note": "; ".join(n for n in (note, p.note) if n),
        "slack_source": source,
    }


def slack(params) -> pd.DataFrame:
    if params.slack_indicator == "vacancy":
        return vacancy_slack(params)
    return ecfin_slack(params)
