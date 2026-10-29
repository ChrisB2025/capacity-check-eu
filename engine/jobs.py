"""Step 3. Required output to persons and hours.

Employment per million euros of output, for each member state and industry:
persons employed (``EMP_DC``, ``THS_PER``) and hours worked (``THS_HW``)
from ``nama_10_a64_e`` for the FIGARO reference year, divided by FIGARO
output for that year. Where national accounts publish no figure for an
industry, the ratio for its NACE section is used and the line is flagged.
Economies outside the EU have output requirements but no jobs estimate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine import concordance
from engine.io_model import Model
from engine.sources._common import EU27, PROCESSED_DIR

BASIS_A64 = "A64"
BASIS_SECTION = "section ratio"
BASIS_MISSING = "missing"


def _nama(year: int, unit: str) -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "nama_10_a64_e.parquet")
    df = df[(df["year"] == year) & (df["na_item"] == "EMP_DC") & (df["unit"] == unit)]
    return df.dropna(subset=["obs_value"])


def coefficients(model: Model, countries=EU27) -> pd.DataFrame:
    """Persons and hours per MEUR of output, by member state and industry."""
    a64 = concordance.load()
    out_rows = []
    for unit, label in (("THS_PER", "persons"), ("THS_HW", "hours")):
        nama = _nama(model.year, unit)
        values = {
            (g, n): v * 1000.0
            for g, n, v in zip(
                nama["geo"], nama["nace_r2"], nama["obs_value"], strict=True
            )
        }
        flags = {
            (g, n): f
            for g, n, f in zip(
                nama["geo"], nama["nace_r2"], nama["obs_flag"], strict=True
            )
        }
        for c in countries:
            x_section: dict[str, float] = {}
            for r in a64.itertuples():
                x_section[r.nace_section] = x_section.get(r.nace_section, 0.0) + float(
                    model.x[model.position(c, r.figaro_code)]
                )
            for r in a64.itertuples():
                x = float(model.x[model.position(c, r.figaro_code)])
                level = values.get((c, r.nama_code))
                if level is not None:
                    basis, flag = BASIS_A64, flags.get((c, r.nama_code), "")
                    coef = level / x if x > 0 else np.nan
                else:
                    sec = values.get((c, r.nace_section))
                    xs = x_section.get(r.nace_section, 0.0)
                    if sec is not None and xs > 0:
                        basis, flag = BASIS_SECTION, flags.get((c, r.nace_section), "")
                        coef = sec / xs
                        level = coef * x
                    else:
                        basis, flag, coef = BASIS_MISSING, "", np.nan
                out_rows.append(
                    {
                        "economy": c,
                        "industry": r.figaro_code,
                        "measure": label,
                        "employment": level,
                        "output_meur": x,
                        "per_meur": coef,
                        "basis": basis,
                        "publisher_flag": (flag or "").strip(),
                    }
                )
    long = pd.DataFrame(out_rows)
    wide = long.pivot_table(
        index=["economy", "industry"],
        columns="measure",
        values=["employment", "per_meur", "basis", "publisher_flag"],
        aggfunc="first",
    )
    wide.columns = [f"{m}_{v}" for v, m in wide.columns]
    wide = wide.reset_index()
    out = wide.merge(
        long[long["measure"] == "persons"][["economy", "industry", "output_meur"]],
        on=["economy", "industry"],
    )
    for col in (
        "persons_employment",
        "hours_employment",
        "persons_per_meur",
        "hours_per_meur",
    ):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def extra_jobs(required_meur: np.ndarray, model: Model, coefs: pd.DataFrame):
    """Extra persons and hours for a vector of required output (MEUR)."""
    pos = [
        model.position(e, i)
        for e, i in zip(coefs["economy"], coefs["industry"], strict=True)
    ]
    req = required_meur[pos]
    return (
        req,
        req * coefs["persons_per_meur"].to_numpy(),
        req * coefs["hours_per_meur"].to_numpy(),
    )
