"""Konjunkturinstitutet business tendency survey, construction, monthly.

Table ``KonjBar/ftgmanad/Barboam.px``: limiting factors (questions 1081 to
1087; 1084 is labour) by SNI 41, 42, 43 and construction as a whole. Used to
cross-check the DG ECFIN construction series for Sweden, which Konjunktur-
institutet supplies as the Commission's Swedish partner institute.
"""

from __future__ import annotations

from engine.sources import pxweb
from engine.sources._common import SourceError, record, write_parquet

TABLE = "https://statistik.konj.se/PxWeb/api/v1/sv/KonjBar/ftgmanad/Barboam.px"
PUBLISHER = "Konjunkturinstitutet (NIER)"
LICENCE = "not stated by the publisher; to be confirmed (see gate-1 report)"
LIMITING = ["1081", "1082", "1083", "1084", "1085", "1086", "1087"]


def load(force: bool = False):
    raw = pxweb.query(
        "konj_construction",
        TABLE,
        "konj-barboam",
        {
            "Bransch (SNI 2007)": ["*"],
            "Fråga": LIMITING,
            "Serie": ["*"],
            "Period": ["*"],
        },
        force=force,
    )
    df = pxweb.read_jsonstat2(raw.path)
    df.columns = [
        c.replace("Bransch (SNI 2007)", "sector")
        .replace("Fråga", "question")
        .replace("Serie", "series")
        .replace("Period", "period")
        for c in df.columns
    ]
    labour = df[(df["question"] == "1084")].dropna(subset=["value"])
    if labour.empty:
        raise SourceError("Barboam: no values for question 1084 (labour)")
    checks = {
        "sectors": sorted(labour["sector"].unique()),
        "series": sorted(labour["series"].unique()),
        "first_period": labour["period"].min(),
        "last_period": labour["period"].max(),
    }
    record(raw, PUBLISHER, LICENCE)
    out = write_parquet(df, "konj_barboam", [raw])
    return raw, out, checks
