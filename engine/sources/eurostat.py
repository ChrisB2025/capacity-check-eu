"""Eurostat datasets fetched through the SDMX 2.1 dissemination API.

National accounts employment by 64 industries (``nama_10_a64_e``), GDP
(``nama_10_gdp``) and quarterly job vacancy statistics (``jvs_q_nace2``).
Each dataset is saved whole as compressed SDMX-CSV, so the raw file is the
publisher's full release on the day of download, and filtered afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from engine.sources._common import (
    EU27,
    RawFile,
    SourceError,
    download,
    http_session,
    record,
    write_parquet,
)

API = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"
PUBLISHER = "Eurostat"
LICENCE = (
    "Eurostat reuse policy: reuse with acknowledgement of the source "
    "(Commission Decision 2011/833/EU)"
)
FLAG_MEANINGS = {
    "b": "break in time series",
    "c": "confidential",
    "d": "definition differs",
    "e": "estimated",
    "f": "forecast",
    "n": "not significant",
    "p": "provisional",
    "u": "low reliability",
    "z": "not applicable",
}


def last_update(code: str, sess=None) -> str:
    """Date Eurostat last updated the data of ``code``, as YYYY-MM-DD."""
    sess = sess or http_session()
    resp = sess.get(f"{API}/dataflow/ESTAT/{code}", params={"format": "JSON"})
    if resp.status_code != 200:
        raise SourceError(f"{code}: HTTP {resp.status_code} reading dataflow")
    for ann in resp.json().get("extension", {}).get("annotation", []):
        if ann.get("type") == "DISSEMINATION_TIMESTAMP_DATA":
            return ann["date"][:10]
    raise SourceError(f"{code}: no data timestamp in dataflow annotations")


def fetch(
    key: str, code: str, *, sdmx_key: str = "", params=None, force=False
) -> RawFile:
    """Download a whole dataset (or a key slice) as gzipped SDMX-CSV."""
    sess = http_session()
    edition = f"upd{last_update(code, sess)}"
    query = {"format": "SDMX-CSV", "compressed": "true", **(params or {})}
    url = f"{API}/data/{code}/{sdmx_key}" if sdmx_key else f"{API}/data/{code}"
    return download(
        key, url, code, edition, "csv.gz", params=query, sess=sess, force=force
    )


def read_sdmx_csv(path, usecols=None) -> pd.DataFrame:
    """Read an SDMX-CSV file into a frame with lower-case column names."""
    df = pd.read_csv(
        path, compression="infer", dtype=str, keep_default_na=False, usecols=usecols
    )
    df.columns = [c.lower() for c in df.columns]
    df = df.drop(columns=["dataflow", "last update"], errors="ignore")
    df["obs_value"] = pd.to_numeric(df["obs_value"].replace("", None), errors="coerce")
    return df


def flag_summary(df: pd.DataFrame) -> str:
    """Count observations by publisher flag, for the register."""
    flags = df["obs_flag"].fillna("").str.strip()
    counts = flags[flags != ""].value_counts()
    if counts.empty:
        return "none"
    parts = []
    for flag, n in counts.items():
        meaning = ", ".join(FLAG_MEANINGS.get(ch, ch) for ch in flag)
        parts.append(f"{flag} ({meaning}): {n}")
    return "; ".join(parts)


@dataclass
class Result:
    raw: RawFile
    processed: str
    checks: dict


# Employment by 64 industries -------------------------------------------------


def employment(force=False) -> Result:
    raw = fetch("nama_10_a64_e", "nama_10_a64_e", force=force)
    df = read_sdmx_csv(raw.path)
    df = df[
        df["geo"].isin(EU27)
        & df["unit"].isin(["THS_PER", "THS_HW"])
        & df["na_item"].isin(["EMP_DC", "SAL_DC"])
    ]
    df = df.assign(year=df.pop("time_period").astype(int))
    df = df[df["year"] >= 2010].drop(columns=["freq"])
    checks = validate_employment(df)
    flags = flag_summary(df)
    record(raw, PUBLISHER, LICENCE, f"EU27 rows from 2010: {flags}")
    out = write_parquet(df, "nama_10_a64_e", [raw], filter="EU27, 2010 onward")
    return Result(raw, str(out), checks)


def validate_employment(df: pd.DataFrame, year: int = 2024) -> dict:
    sel = df[(df["year"] == year) & (df["na_item"] == "EMP_DC")]
    if sel.empty:
        raise SourceError(f"nama_10_a64_e: no EMP_DC observations for {year}")
    have = sel.dropna(subset=["obs_value"])
    by_country = (
        have.groupby(["geo", "unit"])["nace_r2"].nunique().unstack("unit").fillna(0)
    )
    missing = sorted(set(EU27) - set(have["geo"]))
    return {
        "year": year,
        "countries_missing": missing,
        "industry_codes_with_values": by_country.astype(int).to_dict(orient="index"),
    }


# GDP ---------------------------------------------------------------------------


def gdp(force=False) -> Result:
    raw = fetch("nama_10_gdp", "nama_10_gdp", sdmx_key="A.CP_MEUR.B1GQ.", force=force)
    df = read_sdmx_csv(raw.path)
    df = df.assign(year=df.pop("time_period").astype(int)).drop(columns=["freq"])
    df = df[df["geo"].isin(EU27) & (df["year"] >= 2010)]
    sel = df[df["year"] == 2024].dropna(subset=["obs_value"])
    missing = sorted(set(EU27) - set(sel["geo"]))
    if missing:
        raise SourceError(f"nama_10_gdp: no 2024 GDP for {missing}")
    flags = flag_summary(df[df["year"] == 2024])
    record(raw, PUBLISHER, LICENCE, f"2024 EU27: {flags}")
    out = write_parquet(df, "nama_10_gdp", [raw], filter="CP_MEUR B1GQ, EU27")
    return Result(raw, str(out), {"countries_with_2024": len(sel)})


# Job vacancies -------------------------------------------------------------------


def vacancies(force=False) -> Result:
    raw = fetch("jvs_q_nace2", "jvs_q_nace2", force=force)
    df = read_sdmx_csv(raw.path)
    keep = df["geo"].isin(EU27) & (df["indic_em"] == "JVR")
    df = df[keep & (df["sizeclas"] == "TOTAL")].drop(columns=["freq"])
    df = df.rename(columns={"time_period": "period"})
    if df.empty:
        raise SourceError("jvs_q_nace2: no JVR observations for EU27")
    checks = {
        "countries": sorted(df["geo"].unique()),
        "nace_codes": sorted(df["nace_r2"].unique()),
        "first_period": df["period"].min(),
        "last_period": df["period"].max(),
    }
    record(raw, PUBLISHER, LICENCE, f"EU27 JVR, all size classes: {flag_summary(df)}")
    out = write_parquet(df, "jvs_q_nace2", [raw], filter="EU27, JVR, sizeclas TOTAL")
    return Result(raw, str(out), checks)
