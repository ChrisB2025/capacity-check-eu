"""Step 2. Leontief analysis on the FIGARO inter-country table.

The table is arranged as 50 economies (49 plus rest of world) by 64 industries,
3,200 rows and columns, in a fixed order: economies alphabetically with rest
of world last, industries in concordance order. Technical coefficients are
``A = Z / x`` by column; the Leontief inverse ``L = (I - A)^-1`` is computed
once per edition and reference year and cached in ``data/processed/``.
Required output for a final demand vector ``y`` is ``L @ y``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from engine import concordance
from engine.sources._common import PROCESSED_DIR, read_provenance, sha256_file
from engine.sources.figaro import FINAL_DEMAND, REST_OF_WORLD, VALUE_ADDED_ORIGIN


@dataclass
class Table:
    """The inter-country table as dense arrays, with its index."""

    economies: list[str]
    industries: list[str]
    Z: np.ndarray  # intermediate flows, rows supply, columns use (MEUR)
    F: pd.DataFrame  # final demand: rows (economy, industry), cols (dest, cat)
    x: np.ndarray  # total output by (economy, industry)
    source: Path
    source_sha256: str

    @property
    def index(self) -> pd.MultiIndex:
        return pd.MultiIndex.from_product(
            [self.economies, self.industries], names=["economy", "industry"]
        )

    def position(self, economy: str, industry: str) -> int:
        return self.economies.index(economy) * len(self.industries) + (
            self.industries.index(industry)
        )


def table_path(edition: str, year: int) -> Path:
    return PROCESSED_DIR / f"figaro_{edition}_y{year}.parquet"


def load_table(edition: str, year: int) -> Table:
    path = table_path(edition, year)
    if not path.exists():
        raise FileNotFoundError(f"{path} missing; run python -m engine fetch")
    df = pd.read_parquet(
        path, columns=["c_orig", "ind_ava", "c_dest", "ind_use", "value"]
    )
    industries = concordance.load()["figaro_code"].tolist()
    inter = df[df["c_orig"] != VALUE_ADDED_ORIGIN]
    economies = sorted(set(inter["c_orig"].astype(str)) - {REST_OF_WORLD})
    economies.append(REST_OF_WORLD)

    n_e, n_i = len(economies), len(industries)
    e_pos = {e: k for k, e in enumerate(economies)}
    i_pos = {i: k for k, i in enumerate(industries)}

    row = (
        inter["c_orig"].astype(str).map(e_pos).to_numpy() * n_i
        + inter["ind_ava"].astype(str).map(i_pos).to_numpy()
    )
    is_fd = inter["ind_use"].isin(FINAL_DEMAND).to_numpy()

    z = inter[~is_fd]
    zr = row[~is_fd]
    zc = (
        z["c_dest"].astype(str).map(e_pos).to_numpy() * n_i
        + z["ind_use"].astype(str).map(i_pos).to_numpy()
    )
    Z = np.zeros((n_e * n_i, n_e * n_i))
    np.add.at(Z, (zr, zc), z["value"].to_numpy())

    f = inter[is_fd]
    F = (
        pd.DataFrame(
            {
                "row": row[is_fd],
                "dest": f["c_dest"].astype(str).to_numpy(),
                "cat": f["ind_use"].astype(str).to_numpy(),
                "value": f["value"].to_numpy(),
            }
        )
        .pivot_table(
            index="row",
            columns=["dest", "cat"],
            values="value",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reindex(range(n_e * n_i), fill_value=0.0)
    )
    x = Z.sum(axis=1) + F.to_numpy().sum(axis=1)
    prov = read_provenance(path)
    sha = prov["sources"][0]["sha256"] if prov.get("sources") else sha256_file(path)
    return Table(economies, industries, Z, F, x, path, sha)


def technical_coefficients(Z: np.ndarray, x: np.ndarray) -> np.ndarray:
    """A = Z / x by column; industries with no output get a zero column."""
    with np.errstate(divide="ignore", invalid="ignore"):
        A = np.where(x > 0, Z / x, 0.0)
    return A


def leontief_inverse(Z: np.ndarray, x: np.ndarray) -> np.ndarray:
    A = technical_coefficients(Z, x)
    n = A.shape[0]
    return np.linalg.solve(np.eye(n) - A, np.eye(n))


def _cache_paths(edition: str, year: int) -> tuple[Path, Path]:
    stem = PROCESSED_DIR / f"leontief_{edition}_y{year}"
    return stem.with_suffix(".npy"), stem.with_suffix(".json")


def cached_inverse(table: Table, edition: str, year: int) -> np.ndarray:
    """The Leontief inverse for this table, computed once and cached."""
    npy, meta = _cache_paths(edition, year)
    if npy.exists() and meta.exists():
        info = json.loads(meta.read_text(encoding="utf-8"))
        if info.get("source_sha256") == table.source_sha256:
            return np.load(npy)
    L = leontief_inverse(table.Z, table.x)
    np.save(npy, L)
    meta.write_text(
        json.dumps(
            {
                "edition": edition,
                "reference_year": year,
                "source_file": table.source.name,
                "source_sha256": table.source_sha256,
                "economies": table.economies,
                "industries": table.industries,
                "inverse_sha256": sha256_file(npy),
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    return L


@dataclass
class Model:
    """Everything a run needs from one edition and year, loaded from cache."""

    edition: str
    year: int
    economies: list[str]
    industries: list[str]
    L: np.ndarray
    x: np.ndarray
    F: np.ndarray  # final demand, rows (economy, industry), cols fd_columns
    fd_columns: list[tuple[str, str]]  # (destination economy, category)
    source_file: str
    source_sha256: str

    def position(self, economy: str, industry: str) -> int:
        return self.economies.index(economy) * len(self.industries) + (
            self.industries.index(industry)
        )


def model(edition: str, year: int) -> Model:
    """Load the cached model, building the cache from the table if needed."""
    npy, meta = _cache_paths(edition, year)
    extra = npy.with_name(npy.stem + "_fd.npz")
    if not (npy.exists() and meta.exists() and extra.exists()):
        table = load_table(edition, year)
        cached_inverse(table, edition, year)
        np.savez(
            extra,
            x=table.x,
            F=table.F.to_numpy(),
            fd_dest=np.array([c[0] for c in table.F.columns]),
            fd_cat=np.array([c[1] for c in table.F.columns]),
        )
    info = json.loads(meta.read_text(encoding="utf-8"))
    with np.load(extra) as z:
        x, F = z["x"], z["F"]
        cols = list(zip(z["fd_dest"].tolist(), z["fd_cat"].tolist(), strict=True))
    return Model(
        edition,
        year,
        info["economies"],
        info["industries"],
        np.load(npy),
        x,
        F,
        cols,
        info["source_file"],
        info["source_sha256"],
    )
