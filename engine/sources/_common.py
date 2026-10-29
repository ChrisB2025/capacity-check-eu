"""Shared helpers for the source modules.

Paths, HTTP with retries, checksums, the data register, and parquet files that
carry their provenance. Every processed table records the raw files it was
built from, with their checksums, inside the parquet schema metadata, so any
number can be traced back to a dataset, an edition and a checksum.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from engine import __version__

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", REPO_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REGISTER_MD = REPO_ROOT / "docs" / "data-register.md"
CHECKSUMS = REPO_ROOT / "data" / "checksums.txt"

USER_AGENT = (
    f"capacity-check-eu/{__version__} "
    "(+https://github.com/ChrisB2025/capacity-check-eu)"
)
PROVENANCE_KEY = b"capacity_check_provenance"

EU27 = (
    "AT",
    "BE",
    "BG",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "EL",
    "ES",
    "FI",
    "FR",
    "HR",
    "HU",
    "IE",
    "IT",
    "LT",
    "LU",
    "LV",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SE",
    "SI",
    "SK",
)


class SourceError(RuntimeError):
    """A source could not be fetched, parsed or validated."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def http_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    sess = requests.Session()
    sess.headers["User-Agent"] = USER_AGENT
    sess.mount("https://", HTTPAdapter(max_retries=retry))
    return sess


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "-", text).strip("-").lower()


@dataclass(frozen=True)
class RawFile:
    """A file saved unedited in ``data/raw/``."""

    key: str
    dataset: str
    edition: str
    url: str
    downloaded: str
    path: Path
    sha256: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "dataset": self.dataset,
            "edition": self.edition,
            "url": self.url,
            "downloaded": self.downloaded,
            "file": self.path.name,
            "sha256": self.sha256,
        }


def raw_path(dataset: str, edition: str, day: dt.date, ext: str) -> Path:
    return RAW_DIR / f"{slug(dataset)}_{slug(edition)}_{day:%Y%m%d}.{ext}"


def find_raw(dataset: str, edition: str, ext: str) -> Path | None:
    """Latest raw file already held for this dataset and edition, if any."""
    pattern = f"{slug(dataset)}_{slug(edition)}_*.{ext}"
    hits = sorted(RAW_DIR.glob(pattern))
    return hits[-1] if hits else None


def _download_date(path: Path) -> str:
    stamp = path.stem.rsplit("_", 1)[-1].split(".")[0]
    try:
        return dt.datetime.strptime(stamp, "%Y%m%d").date().isoformat()
    except ValueError:
        return ""


def download(
    key: str,
    url: str,
    dataset: str,
    edition: str,
    ext: str,
    *,
    params: dict | None = None,
    sess: requests.Session | None = None,
    force: bool = False,
    method: str = "GET",
    json_body: dict | None = None,
) -> RawFile:
    """Download ``url`` into ``data/raw/`` unless this edition is already held."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    held = None if force else find_raw(dataset, edition, ext)
    if held is not None:
        return RawFile(
            key, dataset, edition, url, _download_date(held), held, sha256_file(held)
        )
    sess = sess or http_session()
    now = utc_now()
    dest = raw_path(dataset, edition, now.date(), ext)
    tmp = dest.with_suffix(dest.suffix + ".part")
    resp = sess.request(
        method, url, params=params, json=json_body, stream=True, timeout=600
    )
    if resp.status_code != 200:
        raise SourceError(f"{key}: HTTP {resp.status_code} from {resp.url}")
    with open(tmp, "wb") as fh:
        for chunk in resp.iter_content(1 << 20):
            fh.write(chunk)
    tmp.replace(dest)
    full_url = resp.url if method == "GET" else url
    return RawFile(
        key, dataset, edition, full_url, now.isoformat(), dest, sha256_file(dest)
    )


def import_file(key: str, src: Path, dataset: str, edition: str, note: str) -> RawFile:
    """Copy a manually downloaded file into ``data/raw/`` unedited."""
    if not src.is_file():
        raise SourceError(f"{key}: no such file {src}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ext = "".join(src.suffixes).lstrip(".") or "bin"
    now = utc_now()
    dest = raw_path(dataset, edition, now.date(), ext)
    shutil.copy2(src, dest)
    digest = sha256_file(dest)
    return RawFile(key, dataset, edition, note, now.isoformat(), dest, digest)


def _cell(text: str) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def record(raw: RawFile, publisher: str, licence: str, flags: str = "") -> None:
    """Add the raw file to ``data/checksums.txt`` and the data register, once."""
    CHECKSUMS.parent.mkdir(parents=True, exist_ok=True)
    line = f"{raw.sha256}  {raw.path.name}\n"
    existing = CHECKSUMS.read_text(encoding="utf-8") if CHECKSUMS.exists() else ""
    if line not in existing:
        with open(CHECKSUMS, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)

    register = REGISTER_MD.read_text(encoding="utf-8")
    if raw.sha256 in register:
        return
    row = "| " + " | ".join(
        _cell(v)
        for v in (
            raw.key,
            publisher,
            raw.dataset,
            raw.edition,
            raw.url,
            raw.downloaded,
            raw.path.name,
            raw.sha256,
            licence,
            flags or "none",
        )
    )
    with open(REGISTER_MD, "a", encoding="utf-8", newline="\n") as fh:
        if not register.endswith("\n"):
            fh.write("\n")
        fh.write(row + " |\n")


def write_parquet(
    df: pd.DataFrame, name: str, sources: Iterable[RawFile], **meta
) -> Path:
    """Write ``df`` to ``data/processed/<name>.parquet`` with its provenance."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    provenance = {
        "engine_version": __version__,
        "written": utc_now().isoformat(),
        "sources": [s.as_dict() for s in sources],
        **meta,
    }
    table = pa.Table.from_pandas(df, preserve_index=False)
    table = table.replace_schema_metadata(
        {**(table.schema.metadata or {}), PROVENANCE_KEY: json.dumps(provenance)}
    )
    path = PROCESSED_DIR / f"{name}.parquet"
    pq.write_table(table, path, compression="zstd")
    return path


def read_provenance(path: Path) -> dict:
    meta = pq.read_schema(path).metadata or {}
    return json.loads(meta.get(PROVENANCE_KEY, b"{}"))
