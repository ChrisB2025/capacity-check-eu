"""Arbetsförmedlingen Yrkesbarometer: five-year occupational outlook, open data.

One row per Yrkesbarometer occupation and county (``lan`` "00" is national),
with job prospects, the recruitment situation and the five-year demand
outlook, all as categories. SSYK 2012 four-digit codes link it to the
Statistics Sweden register.
"""

from __future__ import annotations

import json

import pandas as pd

from engine.sources._common import SourceError, download, record, write_parquet

URL = "https://data.jobtechdev.se/prognoser/yrkesbarometer.json"
RELATIONS_URL = "https://data.jobtechdev.se/prognoser/yrkesbarometer_relationer.json"
PUBLISHER = "Arbetsförmedlingen (Swedish Public Employment Service)"
LICENCE = "CC0 1.0 (DCAT metadata of the dataset)"
NATIONAL = "00"
KEEP = [
    "omgang", "yrkesomrade", "yb_yrke", "yb_concept_id", "lan", "ssyk",
    "ssyk_text", "antal_ssyk", "del_av_ssyk", "delvis_helt", "jobbmojligheter",
    "rekryteringssituation", "prognos", "hogsta_bedomningsniva",
]  # fmt: skip


def load(force: bool = False):
    # The round (omgang) is only known after reading the file, so the raw file
    # is named by download date; the round goes in the register.
    raw = download("af_yrkesbarometer", URL, "af-yrkesbarometer", "current", "json",
                   force=force)  # fmt: skip
    rel = download(
        "af_yrkesbarometer_relationer",
        RELATIONS_URL,
        "af-yrkesbarometer-relationer",
        "current",
        "json",
        force=force,
    )
    with open(raw.path, encoding="utf-8-sig") as fh:
        rows = json.load(fh)
    if not isinstance(rows, list) or not rows:
        raise SourceError("Yrkesbarometer: expected a non-empty list")
    df = pd.DataFrame(rows)
    missing = set(KEEP) - set(df.columns)
    if missing:
        raise SourceError(f"Yrkesbarometer: fields missing {sorted(missing)}")
    df = df[KEEP]
    rounds = sorted(df["omgang"].unique())
    national = df[df["lan"] == NATIONAL]
    checks = {
        "rounds": rounds,
        "occupations_national": int(national["yb_yrke"].nunique()),
        "ssyk_codes_national": int(national["ssyk"].nunique()),
        "counties": int(df["lan"].nunique()),
    }
    flags = f"round {', '.join(rounds)}"
    record(raw, PUBLISHER, LICENCE, flags)
    record(rel, PUBLISHER, LICENCE, flags)
    out = write_parquet(df, "af_yrkesbarometer", [raw, rel], rounds=rounds)
    return raw, out, checks
