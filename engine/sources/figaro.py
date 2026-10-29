"""Eurostat FIGARO inter-country input-output tables, industry by industry.

Two loaders:

* ``fetch_sdmx`` downloads the current edition from the Eurostat SDMX API,
  one origin economy at a time, and bundles the unedited responses for one
  reference year into a single zip in ``data/raw/``. The API only ever serves
  the current edition, so the zip is the only lasting copy.
* ``import_circabc`` registers a FIGARO file downloaded by hand from the
  CIRCABC FIGARO space, the only place earlier editions are kept. Its parser
  is written once the file's exact layout is seen.

The processed table is long: one row per flow from (origin economy, supplying
industry) to (destination economy, using industry or final demand category).
Value added and taxes sit on rows whose origin is ``DOM``.
"""

from __future__ import annotations

import gzip
import io
import re
import zipfile

import numpy as np
import pandas as pd
from pandas.api.types import union_categoricals

from engine.sources import eurostat
from engine.sources._common import (
    RawFile,
    SourceError,
    _download_date,
    find_raw,
    http_session,
    import_file,
    raw_path,
    record,
    sha256_file,
    utc_now,
    write_parquet,
)

API = eurostat.API
DATASET = "naio_10_fcp"
FINAL_DEMAND = ("P3_S13", "P3_S14", "P3_S15", "P51G", "P5M")
VALUE_ADDED_ORIGIN = "DOM"
REST_OF_WORLD = "WRL_REST"
N_INDUSTRIES = 64
CIRCABC_LIBRARY = (
    "https://circabc.europa.eu/ui/group/cec66924-a924-4f91-a0ef-600a0531e3ba/"
    "library/460a20fc-5956-44f9-8633-2821eb48dd62"
)


def dataflow_for(year: int) -> str:
    if 2010 <= year <= 2013:
        return "naio_10_fcp_ii1"
    if 2014 <= year <= 2017:
        return "naio_10_fcp_ii2"
    if 2018 <= year <= 2021:
        return "naio_10_fcp_ii3"
    if year >= 2022:
        return "naio_10_fcp_ii4"
    raise SourceError(f"FIGARO has no reference year {year}")


def _origins(code: str, year: int, sess) -> list[str]:
    """Origin codes present in the table, read from one destination column."""
    resp = sess.get(
        f"{API}/data/{code}/A.F..SE..",
        params={"startPeriod": year, "endPeriod": year, "format": "SDMX-CSV"},
        timeout=300,
    )
    if resp.status_code != 200:
        raise SourceError(f"{code}: HTTP {resp.status_code} listing origins")
    df = pd.read_csv(io.StringIO(resp.text), dtype=str)
    return sorted(df["c_orig"].unique())


def fetch_sdmx(year: int, edition: str = "2026", force: bool = False) -> RawFile:
    """Download every flow for ``year`` from the API into one raw zip."""
    code = dataflow_for(year)
    sess = http_session()
    updated = eurostat.last_update(code, sess)
    if not updated.startswith(edition):
        raise SourceError(
            f"{code} on the API was updated {updated}; expected the {edition} edition"
        )
    ed = f"{edition}ed-y{year}"
    url_pattern = (
        f"{API}/data/{code}/A.....<c_orig>?startPeriod={year}&endPeriod={year}"
        "&format=SDMX-CSV&compressed=true"
    )
    key = f"figaro_{edition}_y{year}"
    held = None if force else find_raw(DATASET, ed, "zip")
    if held is not None:
        return RawFile(
            key,
            DATASET,
            ed,
            url_pattern,
            _download_date(held),
            held,
            sha256_file(held),
        )

    origins = _origins(code, year, sess)
    now = utc_now()
    dest = raw_path(DATASET, ed, now.date(), "zip")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".zip.part")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_STORED) as zf:
        for c in origins:
            resp = sess.get(
                f"{API}/data/{code}/A.....{c}",
                params={
                    "startPeriod": year,
                    "endPeriod": year,
                    "format": "SDMX-CSV",
                    "compressed": "true",
                },
                timeout=600,
            )
            if resp.status_code != 200:
                raise SourceError(f"{code} origin {c}: HTTP {resp.status_code}")
            zf.writestr(f"{code}_{year}_{c}.csv.gz", resp.content)
        zf.writestr(
            "README.txt",
            f"Eurostat {code}, reference year {year}, data updated {updated}.\n"
            f"One unedited API response per origin economy: {url_pattern}\n"
            f"Downloaded {now.isoformat()}.\n",
        )
    tmp.replace(dest)
    return RawFile(
        key, DATASET, ed, url_pattern, now.isoformat(), dest, sha256_file(dest)
    )


CATEGORICAL = ("c_orig", "ind_ava", "c_dest", "ind_use", "OBS_FLAG")


def parse_sdmx_zip(path) -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith(".csv.gz"):
                continue
            with zf.open(name) as fh:
                raw = gzip.decompress(fh.read())
            frames.append(
                pd.read_csv(
                    io.BytesIO(raw),
                    usecols=[*CATEGORICAL, "OBS_VALUE"],
                    dtype={
                        "OBS_VALUE": "float64",
                        **dict.fromkeys(CATEGORICAL, "category"),
                    },
                    keep_default_na=False,
                    na_values={"OBS_VALUE": [""]},
                )
            )
    if not frames:
        raise SourceError(f"{path}: no API responses inside")
    # Concatenating categoricals with different categories would fall back to
    # Python strings (gigabytes at this size), so union the categories first.
    data = {
        col: union_categoricals([f[col] for f in frames], ignore_order=True)
        for col in CATEGORICAL
    }
    data["OBS_VALUE"] = np.concatenate([f["OBS_VALUE"].to_numpy() for f in frames])
    df = pd.DataFrame(data)
    df = df.rename(columns={"OBS_VALUE": "value", "OBS_FLAG": "flag"})
    return df[["c_orig", "ind_ava", "c_dest", "ind_use", "value", "flag"]]


def validate(df: pd.DataFrame) -> dict:
    """Structural checks and the output identity for every economy and industry."""
    inter_rows = df[df["c_orig"] != VALUE_ADDED_ORIGIN]
    economies = sorted(set(inter_rows["c_orig"].astype(str)))
    industries = sorted(set(inter_rows["ind_ava"].astype(str)))
    uses = set(df["ind_use"].astype(str))
    if len(industries) != N_INDUSTRIES:
        raise SourceError(f"expected {N_INDUSTRIES} industries, got {len(industries)}")
    if not set(FINAL_DEMAND) <= uses:
        absent = set(FINAL_DEMAND) - uses
        raise SourceError(f"final demand categories missing: {absent}")
    missing_values = int(df["value"].isna().sum())

    is_fd = df["ind_use"].isin(FINAL_DEMAND)
    negative_intermediate = int(
        ((df["value"] < 0) & ~is_fd & (df["c_orig"] != VALUE_ADDED_ORIGIN)).sum()
    )

    row_total = (
        inter_rows.groupby(["c_orig", "ind_ava"], observed=True)["value"]
        .sum()
        .reset_index()
        .rename(columns={"c_orig": "economy", "ind_ava": "industry", "value": "row"})
    )
    col_total = (
        df[~is_fd]
        .groupby(["c_dest", "ind_use"], observed=True)["value"]
        .sum()
        .reset_index()
        .rename(columns={"c_dest": "economy", "ind_use": "industry", "value": "col"})
    )
    for t in (row_total, col_total):
        t["economy"] = t["economy"].astype(str)
        t["industry"] = t["industry"].astype(str)
    both = row_total.merge(col_total, on=["economy", "industry"], how="outer")
    both = both.fillna(0.0)
    gap = (both["row"] - both["col"]).abs()
    scale = np.maximum(both[["row", "col"]].abs().max(axis=1), 1.0)
    rel = gap / scale
    worst = both.loc[rel.idxmax(), ["economy", "industry"]]
    flagged_codes = [c for c in df["flag"].cat.categories if str(c).strip()]
    return {
        "economies": len(economies),
        "industries": len(industries),
        "rows": len(df),
        "missing_values": missing_values,
        "negative_intermediate_flows": negative_intermediate,
        "flagged_observations": int(df["flag"].isin(flagged_codes).sum()),
        "output_identity_cells": len(both),
        "output_identity_max_abs_gap_meur": float(gap.max()),
        "output_identity_max_rel_gap": float(rel.max()),
        "output_identity_worst_cell": f"{worst['economy']} {worst['industry']}",
    }


def load_sdmx(year: int, edition: str = "2026", force: bool = False):
    raw = fetch_sdmx(year, edition, force)
    df = parse_sdmx_zip(raw.path)
    checks = validate(df)
    if checks["missing_values"] or checks["output_identity_max_rel_gap"] > 1e-3:
        raise SourceError(f"{raw.key} failed validation: {checks}")
    record(
        raw,
        "Eurostat",
        eurostat.LICENCE,
        f"{checks['flagged_observations']} flagged observations",
    )
    out = write_parquet(
        df,
        f"figaro_{edition}_y{year}",
        [raw],
        edition=edition,
        reference_year=year,
        unit="MIO_EUR",
        checks=checks,
    )
    return raw, out, checks


# CIRCABC flat files ----------------------------------------------------------------

# CIRCABC uses "webpage" codes; the API uses Eurobase codes. The country
# mapping is the one in Eurostat's Description_FIGARO_Tables workbook (sheet
# "Circabc-Eurobase code mapping"). For industry ranges that sheet gives
# "C10-C12", but the API itself serves "C10-12", so the API's form is used.
CIRCABC_AREAS = {"GB": "UK", "GR": "EL", "W2": "DOM", "FIGW1": "WRL_REST"}


def _circabc_code(code: str) -> str:
    return re.sub(r"^([A-Z])(\d{2})T(\d{2})$", r"\1\2-\3", code)


def parse_circabc_flat(path) -> pd.DataFrame:
    """Read a CIRCABC ``flatfile_eu-ic-io_ind-by-ind`` zip into the API schema."""
    import pyarrow as pa
    import pyarrow.csv as pacsv

    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise SourceError(f"{path}: expected one CSV inside, found {names}")
        with zf.open(names[0]) as fh:
            table = pacsv.read_csv(
                fh,
                convert_options=pacsv.ConvertOptions(
                    include_columns=[
                        "refArea",
                        "rowIi",
                        "counterpartArea",
                        "colIi",
                        "obsValue",
                    ],
                    column_types={"obsValue": pa.float64()},
                ),
            )
    df = pd.DataFrame(
        {
            "c_orig": table["refArea"].dictionary_encode().to_pandas(),
            "ind_ava": table["rowIi"].dictionary_encode().to_pandas(),
            "c_dest": table["counterpartArea"].dictionary_encode().to_pandas(),
            "ind_use": table["colIi"].dictionary_encode().to_pandas(),
            "value": table["obsValue"].to_numpy(),
        }
    )
    for col in ("c_orig", "c_dest"):
        df[col] = df[col].cat.rename_categories(lambda c: CIRCABC_AREAS.get(c, c))
    for col in ("ind_ava", "ind_use"):
        df[col] = df[col].cat.rename_categories(_circabc_code)
    df["flag"] = pd.Categorical([""] * len(df))
    return df


def compare(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Flow-by-flow comparison of two copies of the same table."""
    keys = ["c_orig", "ind_ava", "c_dest", "ind_use"]
    left = a[[*keys, "value"]].copy()
    right = b[[*keys, "value"]].copy()
    for t in (left, right):
        for k in keys:
            t[k] = t[k].astype(str)
    merged = left.merge(
        right, on=keys, how="outer", suffixes=("_a", "_b"), indicator=True
    )
    both = merged[merged["_merge"] == "both"]
    diff = (both["value_a"] - both["value_b"]).abs()
    return {
        "rows_a": len(a),
        "rows_b": len(b),
        "only_in_a": int((merged["_merge"] == "left_only").sum()),
        "only_in_b": int((merged["_merge"] == "right_only").sum()),
        "max_abs_diff_meur": float(diff.max()),
        "flows_differing_by_more_than_0_001_meur": int((diff > 0.001).sum()),
    }


def load_circabc(edition: str, year: int):
    """Parse an imported CIRCABC file, validate it and, if the API copy of the
    same edition and year is held, compare the two flow by flow."""
    held = find_raw(f"{DATASET}-circabc", f"{edition}ed-y{year}", "zip")
    if held is None:
        raise SourceError(
            f"no CIRCABC file imported for edition {edition}, year {year}; "
            "run python -m engine import-figaro first"
        )
    raw = RawFile(
        f"figaro_{edition}_y{year}_circabc",
        f"{DATASET}-circabc",
        f"{edition}ed-y{year}",
        f"{CIRCABC_LIBRARY} (manual download)",
        _download_date(held),
        held,
        sha256_file(held),
    )
    df = parse_circabc_flat(raw.path)
    checks = validate(df)
    if checks["missing_values"] or checks["output_identity_max_rel_gap"] > 1e-3:
        raise SourceError(f"{raw.key} failed validation: {checks}")

    from engine.sources._common import PROCESSED_DIR

    api_path = PROCESSED_DIR / f"figaro_{edition}_y{year}.parquet"
    if api_path.exists():
        checks["comparison_with_api_copy"] = compare(df, pd.read_parquet(api_path))
        name = f"figaro_{edition}_y{year}_circabc"
    else:
        name = f"figaro_{edition}_y{year}"
    out = write_parquet(
        df,
        name,
        [raw],
        edition=edition,
        reference_year=year,
        unit="MIO_EUR",
        checks=checks,
        loader="circabc",
    )
    return raw, out, checks


def import_circabc(src, edition: str, year: int) -> RawFile:
    """Register a FIGARO file downloaded by hand from CIRCABC."""
    from pathlib import Path

    raw = import_file(
        f"figaro_{edition}_y{year}_circabc",
        Path(src),
        f"{DATASET}-circabc",
        f"{edition}ed-y{year}",
        f"{CIRCABC_LIBRARY} (manual download)",
    )
    record(raw, "Eurostat", eurostat.LICENCE, "parsed after import; see gate-1 report")
    return raw
