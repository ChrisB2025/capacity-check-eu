"""Statistics Sweden occupational register, through the PxWeb API.

YREG54BAS: employees by 4-digit SSYK 2012 occupation and 16 industry groups.
YREG52BAS: employees by occupation and field of education (SUN 2020, ten
broad fields). Age and sex are eliminated, giving totals.
"""

from __future__ import annotations

import time

import pandas as pd

from engine.sources import pxweb
from engine.sources._common import SourceError, record, write_parquet

BASE = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/AM/AM0208/AM0208E"
PUBLISHER = "Statistics Sweden (SCB)"
LICENCE = "CC0 1.0 (SCB open data); SCB asks to be cited as the source"
UNKNOWN_INDUSTRY = "00"
UNKNOWN_OCCUPATION = "0002"

TABLES = {
    "scb_yreg54bas": ("YREG54BAS", "SNI2007"),
    "scb_yreg52bas": ("YREG52BAS", "UtbinriktnSUN2020"),
}


def load(key: str, force: bool = False):
    table, second = TABLES[key]
    raw = pxweb.query(
        key,
        f"{BASE}/{table}",
        f"scb-{table.lower()}",
        {"Yrke2012": ["*"], second: ["*"], "ContentsCode": ["*"], "Tid": ["*"]},
        force=force,
    )
    df = pxweb.read_jsonstat2(raw.path)
    df = df.rename(
        columns={
            "Yrke2012": "ssyk",
            "Yrke2012_label": "ssyk_label",
            second: "group",
            f"{second}_label": "group_label",
            "Tid": "year",
            "value": "employees",
        }
    )
    df = df[["ssyk", "ssyk_label", "group", "group_label", "year", "employees"]]
    df["year"] = df["year"].astype(int)
    checks = validate(df, table)
    record(raw, PUBLISHER, LICENCE, checks["note"])
    out = write_parquet(df, f"scb_{table.lower()}", [raw], table=table)
    time.sleep(1.1)  # SCB allows ten calls per ten seconds
    return raw, out, checks


def validate(df: pd.DataFrame, table: str) -> dict:
    if df["employees"].isna().all():
        raise SourceError(f"{table}: no values returned")
    years = sorted(int(y) for y in df["year"].unique())
    latest = df[df["year"] == years[-1]]
    total = latest["employees"].sum()
    unknown_occ = latest.loc[latest["ssyk"] == UNKNOWN_OCCUPATION, "employees"].sum()
    checks = {
        "years": years,
        "occupations": int(df["ssyk"].nunique()),
        "groups": int(df["group"].nunique()),
        "suppressed_cells": int(df["employees"].isna().sum()),
        "latest_year_total": float(total),
        "latest_year_unknown_occupation_share": float(unknown_occ / total),
    }
    if table == "YREG54BAS":
        unknown_ind = latest.loc[latest["group"] == UNKNOWN_INDUSTRY, "employees"].sum()
        checks["latest_year_unknown_industry_share"] = float(unknown_ind / total)
    checks["note"] = f"{checks['suppressed_cells']} suppressed or missing cells"
    return checks
