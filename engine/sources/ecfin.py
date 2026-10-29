"""DG ECFIN business surveys: factors limiting activity, by sector.

The Commission publishes each monthly release as zipped Excel workbooks in a
folder named after the release (``nace2_ecfin_YYMM``). Each workbook has an
``Index`` sheet (the code book), an ``INFO`` sheet (revisions and suspensions)
and data sheets whose columns are series codes of the form
``SURVEY.COUNTRY.SECTOR.QUESTION.ANSWER.FREQUENCY``.

The answer code for "shortage of labour" differs between surveys (F4 in
construction, F3 in industry and services), so the labour series is found
from the code book's labels, never from a fixed code.
"""

from __future__ import annotations

import datetime as dt
import io
import re
import zipfile
from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine.sources._common import (
    RawFile,
    SourceError,
    download,
    http_session,
    record,
    write_parquet,
)

PAGE = (
    "https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/"
    "business-and-consumer-surveys/download-business-and-consumer-survey-data/"
    "subsector-data_en"
)
SERIES_BASE = (
    "https://ec.europa.eu/economy_finance/db_indicators/surveys/documents/series"
)
WEIGHTS_URL = (
    "https://economy-finance.ec.europa.eu/document/download/"
    "94e8e226-e091-4cef-8be5-6410142c4cd3_en?filename=user_guide_country_weights.zip"
)
PUBLISHER = "European Commission, DG ECFIN"
LICENCE = (
    "Commission reuse policy, CC BY 4.0 (Commission Decision 2011/833/EU); "
    "publisher notes subsector series are not fully validated"
)
SURVEYS = ("building", "industry", "services", "retail")
SERIES_RE = re.compile(
    r"^(?P<survey>[A-Z]{4})\.(?P<country>[A-Z]{2})\.(?P<sector>[A-Z0-9]+)\."
    r"(?P<question>[A-Z0-9]+)\.(?P<answer>[A-Z0-9]+)\.(?P<freq>[MQ])$"
)
SURVEY_CODE = {
    "BUIL": "building",
    "INDU": "industry",
    "SERV": "services",
    "RETA": "retail",
}


def current_release(sess=None) -> str:
    """Release folder currently linked from the subsector page, e.g. ``2610``."""
    sess = sess or http_session()
    resp = sess.get(PAGE, timeout=120)
    if resp.status_code != 200:
        raise SourceError(f"ECFIN subsector page: HTTP {resp.status_code}")
    found = sorted(set(re.findall(r"nace2_ecfin_(\d{4})/", resp.text)))
    if not found:
        raise SourceError("ECFIN subsector page links no nace2_ecfin_YYMM folder")
    return found[-1]


def file_names() -> list[str]:
    names = []
    for survey in SURVEYS:
        for adj in ("nsa", "sa"):
            names.append(f"{survey}_subsectors_{adj}_nace2.zip")
            names.append(f"{survey}_total_{adj}_nace2.zip")
    return names


def fetch(force: bool = False) -> tuple[str, list[RawFile]]:
    sess = http_session()
    release = current_release(sess)
    raws = []
    for name in file_names():
        stem = name.removesuffix(".zip")
        raws.append(
            download(
                f"ecfin_{stem}",
                f"{SERIES_BASE}/nace2_ecfin_{release}/{name}",
                f"ecfin-{stem}",
                f"rel{release}",
                "zip",
                sess=sess,
                force=force,
            )
        )
    raws.append(
        download(
            "ecfin_country_weights",
            WEIGHTS_URL,
            "ecfin-country-weights",
            f"rel{release}",
            "zip",
            sess=sess,
            force=force,
        )
    )
    return release, raws


# Parsing -----------------------------------------------------------------------


def _period(value, freq: str) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, dt.datetime | dt.date):
        d = value
    elif isinstance(value, int | float):
        d = dt.date(1899, 12, 30) + dt.timedelta(days=int(value))
    else:
        text = str(value).strip()
        m = re.match(r"^(\d{4})-?Q([1-4])$", text)
        if m:
            return f"{m.group(1)}Q{m.group(2)}"
        try:
            d = dt.date.fromisoformat(text[:10])
        except ValueError:
            return None
    if freq == "Q":
        return f"{d.year}Q{(d.month - 1) // 3 + 1}"
    return f"{d.year}-{d.month:02d}"


def parse_codebook(sheet: pd.DataFrame, workbook: str) -> pd.DataFrame:
    """Turn the ``Index`` sheet into rows of (section, code, label)."""
    rows, section = [], None
    for values in sheet.itertuples(index=False):
        cells = [str(v).strip() for v in values if str(v).strip() not in ("", "nan")]
        if len(cells) == 1:
            section = cells[0]
        elif len(cells) >= 2 and section:
            rows.append((workbook, section, cells[0], cells[1]))
    return pd.DataFrame(rows, columns=["workbook", "section", "code", "label"])


def parse_sheet(sheet: pd.DataFrame, workbook: str, adjusted: bool) -> pd.DataFrame:
    header = [str(v).strip() for v in sheet.iloc[0].tolist()]
    cols = [(i, SERIES_RE.match(h)) for i, h in enumerate(header)]
    cols = [(i, m) for i, m in cols if m]
    if not cols:
        return pd.DataFrame()
    freq = cols[0][1].group("freq")
    periods = [_period(v, freq) for v in sheet.iloc[1:, 0].tolist()]
    out = []
    for i, m in cols:
        vals = pd.to_numeric(sheet.iloc[1:, i].replace("NA", np.nan), errors="coerce")
        frame = pd.DataFrame({"period": periods, "value": vals.to_numpy()})
        frame = frame.dropna()
        if frame.empty:
            continue
        frame = frame.assign(series=m.group(0), **m.groupdict())
        out.append(frame)
    if not out:
        return pd.DataFrame()
    df = pd.concat(out, ignore_index=True)
    df["survey"] = df["survey"].map(SURVEY_CODE).fillna(df["survey"])
    df["seasonally_adjusted"] = adjusted
    df["workbook"] = workbook
    return df


def parse_zip(raw: RawFile) -> tuple[pd.DataFrame, pd.DataFrame]:
    adjusted = "_sa_" in raw.key
    series, books = [], []
    with zipfile.ZipFile(raw.path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith((".xlsx", ".xls")):
                continue
            content = io.BytesIO(zf.read(name))
            sheets = pd.read_excel(
                content, sheet_name=None, header=None, engine="calamine", dtype=object
            )
            for sheet_name, sheet in sheets.items():
                if sheet_name == "Index":
                    books.append(parse_codebook(sheet, name))
                elif sheet_name != "INFO":
                    series.append(parse_sheet(sheet, name, adjusted))
    s = pd.concat(series, ignore_index=True) if series else pd.DataFrame()
    b = pd.concat(books, ignore_index=True) if books else pd.DataFrame()
    return s, b


def labour_answers(codebook: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """Map each survey to (question, answer) for 'labour' as a limiting factor."""
    out = {}
    answers = codebook[codebook["section"].str.lower().str.startswith("answers")]
    for wb, grp in answers.groupby("workbook"):
        survey = wb.split("_", 1)[0]
        hit = grp[grp["label"].str.contains(r"\blabour\b", case=False, regex=True)]
        if hit.empty:
            continue
        code, label = hit.iloc[0]["code"], hit.iloc[0]["label"]
        q = re.search(r"question (\d+)", label)
        if q:
            out.setdefault(survey, (q.group(1), code))
    return out


@dataclass
class Result:
    release: str
    raws: list[RawFile]
    processed: str
    codebook: str
    labour: dict


def load(force: bool = False) -> Result:
    release, raws = fetch(force)
    series, books = [], []
    for raw in raws:
        if raw.key == "ecfin_country_weights":
            continue
        s, b = parse_zip(raw)
        series.append(s)
        books.append(b)
    df = pd.concat(series, ignore_index=True)
    codebook = pd.concat(books, ignore_index=True).drop_duplicates()
    df = df.drop_duplicates(
        subset=["series", "period", "seasonally_adjusted"], keep="first"
    )
    for col in (
        "survey",
        "country",
        "sector",
        "question",
        "answer",
        "freq",
        "series",
        "workbook",
    ):
        df[col] = df[col].astype("category")

    labour = labour_answers(codebook)
    for survey in ("building", "industry", "services"):
        if survey not in labour:
            raise SourceError(f"ECFIN {survey}: no labour answer found in code book")

    for raw in raws:
        record(raw, PUBLISHER, LICENCE)
    out = write_parquet(
        df, f"ecfin_bcs_rel{release}", raws, release=release, labour_codes=labour
    )
    cb = write_parquet(codebook, f"ecfin_codebook_rel{release}", raws, release=release)
    return Result(release, raws, str(out), str(cb), labour)


def labour_series(df: pd.DataFrame, labour: dict, adjusted: bool = False):
    """Share of firms naming labour as a limiting factor, every survey."""
    parts = []
    for survey, (question, answer) in labour.items():
        code = f"{answer}S" if adjusted else answer  # SA answers carry an S suffix
        sel = df[
            (df["survey"] == survey)
            & (df["question"] == question)
            & (df["answer"] == code)
            & (df["seasonally_adjusted"] == adjusted)
        ]
        parts.append(sel)
    return pd.concat(parts, ignore_index=True)


def coverage(labour_df: pd.DataFrame, min_obs: int = 1) -> pd.DataFrame:
    """First and last period and observation count, by country and sector."""
    g = labour_df.groupby(["survey", "country", "sector"], observed=True)
    cov = g["period"].agg(first="min", last="max", n="count").reset_index()
    return cov[cov["n"] >= min_obs]
