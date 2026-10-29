"""Step 1. Composition table and direct demand.

A composition is a YAML file in ``engine/compositions/`` that splits the
shock across the products bought directly, using FIGARO industry codes (the
tables are industry by industry, so a purchase of a product is assigned to
the industry with the same code). Each composition carries a status. The
engine refuses to run a composition that has not been confirmed, because the
brief requires the reviewer to see it before any results exist.

Direct demand for member state ``c`` is ``shock_pct / 100 * GDP_c`` split by
the composition shares, then split by origin economy using ``c``'s existing
purchases of that product in the chosen final demand category (gross fixed
capital formation by default).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from engine import concordance
from engine.io_model import Model
from engine.sources._common import EU27, PROCESSED_DIR

COMPOSITION_DIR = Path(__file__).resolve().parent / "compositions"
SHARE_TOLERANCE = 1e-9


class CompositionNotConfirmed(RuntimeError):
    """Raised when a run uses a composition the reviewer has not seen."""


@dataclass(frozen=True)
class Line:
    code: str
    share: float
    label: str
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class Composition:
    name: str
    status: str
    lines: tuple[Line, ...]
    confirmed_by: str | None = None
    confirmed_on: str | None = None
    description: str = ""
    meta: dict = field(default_factory=dict, compare=False)

    def validate(self) -> None:
        codes = set(concordance.FIGARO_A64)
        unknown = [ln.code for ln in self.lines if ln.code not in codes]
        if unknown:
            raise ValueError(f"composition {self.name}: unknown codes {unknown}")
        if any(ln.share < 0 for ln in self.lines):
            raise ValueError(f"composition {self.name}: negative share")
        total = sum(ln.share for ln in self.lines)
        if abs(total - 1.0) > SHARE_TOLERANCE:
            raise ValueError(f"composition {self.name}: shares sum to {total}, not 1")
        if len({ln.code for ln in self.lines}) != len(self.lines):
            raise ValueError(f"composition {self.name}: duplicate codes")

    def require_confirmed(self) -> None:
        if self.status != "confirmed":
            raise CompositionNotConfirmed(
                f"composition '{self.name}' has status '{self.status}'. Results "
                "are run only after the reviewer has seen it and Chris has "
                "confirmed it (set status: confirmed, confirmed_by, confirmed_on)."
            )


def composition_path(name: str | Path) -> Path:
    """A composition by name (in engine/compositions/) or by file path."""
    p = Path(name)
    return p if p.suffix == ".yaml" else COMPOSITION_DIR / f"{name}.yaml"


def load_composition(name: str | Path) -> Composition:
    path = composition_path(name)
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    comp = Composition(
        name=raw["name"],
        status=raw.get("status", "proposed"),
        lines=tuple(
            Line(
                str(ln["code"]),
                float(ln["share"]),
                ln.get("label", ""),
                tuple(ln.get("sources", [])),
            )
            for ln in raw["lines"]
        ),
        confirmed_by=raw.get("confirmed_by"),
        confirmed_on=str(raw["confirmed_on"]) if raw.get("confirmed_on") else None,
        description=raw.get("description", ""),
        meta={k: v for k, v in raw.items() if k not in ("lines",)},
    )
    comp.validate()
    return comp


def gdp_meur(year: int, countries=EU27) -> dict[str, float]:
    df = pd.read_parquet(PROCESSED_DIR / "nama_10_gdp.parquet")
    df = df[(df["year"] == year) & df["geo"].isin(countries)].dropna(
        subset=["obs_value"]
    )
    out = dict(zip(df["geo"], df["obs_value"].astype(float), strict=True))
    missing = set(countries) - set(out)
    if missing:
        raise ValueError(f"no {year} GDP for {sorted(missing)}")
    return out


def origin_shares(
    model: Model, dest: str, code: str, category: str
) -> tuple[np.ndarray, str]:
    """Share of ``dest``'s purchases of ``code`` coming from each economy.

    Uses the ``category`` column of final demand; falls back to all final
    demand categories of ``dest``, then to all-domestic, and says which.
    """
    rows = [model.position(e, code) for e in model.economies]
    cols = [
        k for k, (d, c) in enumerate(model.fd_columns) if d == dest and c == category
    ]
    flows = model.F[np.ix_(rows, cols)].sum(axis=1) if cols else np.zeros(len(rows))
    basis = category
    if flows.sum() <= 0:
        cols = [k for k, (d, _) in enumerate(model.fd_columns) if d == dest]
        flows = model.F[np.ix_(rows, cols)].sum(axis=1)
        basis = "all final demand"
    if flows.sum() <= 0:
        flows = np.array([1.0 if e == dest else 0.0 for e in model.economies])
        basis = "assumed domestic"
    flows = np.clip(flows, 0.0, None)  # inventory changes can be negative
    return flows / flows.sum(), basis


@dataclass
class DirectDemand:
    """Direct purchases for one shocking member state."""

    country: str
    amount_meur: float
    y: np.ndarray  # final demand vector over (economy, industry)
    by_product: pd.DataFrame  # code, share, meur, home, rest_eu, non_eu, basis


def direct_demand(
    model: Model,
    composition: Composition,
    country: str,
    gdp: float,
    shock_pct: float,
    import_basis: str = "P51G",
    eu: tuple[str, ...] = EU27,
) -> DirectDemand:
    amount = shock_pct / 100.0 * gdp
    y = np.zeros(len(model.economies) * len(model.industries))
    rows = []
    for ln in composition.lines:
        spend = amount * ln.share
        shares, basis = origin_shares(model, country, ln.code, import_basis)
        for k, econ in enumerate(model.economies):
            y[model.position(econ, ln.code)] += spend * shares[k]
        home = shares[model.economies.index(country)]
        rest_eu = sum(
            shares[k] for k, e in enumerate(model.economies) if e in eu and e != country
        )
        rows.append(
            {
                "code": ln.code,
                "share": ln.share,
                "meur": spend,
                "home": home,
                "rest_eu": rest_eu,
                "non_eu": 1.0 - home - rest_eu,
                "origin_basis": basis,
            }
        )
    return DirectDemand(country, amount, y, pd.DataFrame(rows))
