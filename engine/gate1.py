"""Gate 1 evidence: coverage tables built from the registered processed files.

``python -m engine gate1`` writes CSV tables to ``docs/gate-1/`` and a
``SOURCES.md`` listing the raw files and checksums every table derives from.
Nothing here is estimated; the tables count and date what the files contain.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from engine import concordance
from engine.sources import ecfin
from engine.sources._common import EU27, PROCESSED_DIR, REPO_ROOT, read_provenance

OUT_DIR = REPO_ROOT / "docs" / "gate-1"
HISTORY_YEARS = (5, 10)  # history lengths reported; a parameter, not a rule
DIRECT_SHOCK_INDUSTRIES = ("F", "C16", "C22", "C23", "C25", "C27", "C28", "M71")


def _processed(name_glob: str) -> Path:
    hits = sorted(PROCESSED_DIR.glob(f"{name_glob}.parquet"))
    if not hits:
        raise FileNotFoundError(f"no processed file matching {name_glob}")
    return hits[-1]


def _to_period(s: pd.Series, freq: str) -> pd.PeriodIndex:
    if freq == "Q":
        return pd.PeriodIndex(s.str.replace("Q", "-Q", regex=False), freq="Q")
    return pd.PeriodIndex(s, freq="M")


# ECFIN -------------------------------------------------------------------------


def ecfin_coverage() -> tuple[pd.DataFrame, Path]:
    path = _processed("ecfin_bcs_rel*")
    labour_codes = read_provenance(path)["labour_codes"]
    cols = [
        "survey",
        "country",
        "sector",
        "question",
        "answer",
        "freq",
        "period",
        "value",
        "seasonally_adjusted",
    ]
    df = pd.read_parquet(path, columns=cols)
    lab = ecfin.labour_series(df, labour_codes, adjusted=False)
    lab = lab[lab["country"].isin(EU27)]
    rows = []
    for (survey, country, sector), g in lab.groupby(
        ["survey", "country", "sector"], observed=True
    ):
        freq = g["freq"].iloc[0]
        per = _to_period(g["period"].astype(str), freq).sort_values()
        span = pd.period_range(per[0], per[-1], freq=per.freq)
        per_year = 4 if freq == "Q" else 12
        rows.append(
            {
                "survey": survey,
                "country": country,
                "sector": sector,
                "frequency": freq,
                "first": str(per[0]),
                "last": str(per[-1]),
                "observations": len(per),
                "gaps_within_span": len(span) - len(per),
                "years_of_observations": round(len(per) / per_year, 1),
            }
        )
    return pd.DataFrame(rows), path


def ecfin_a64(cov: pd.DataFrame, a64: pd.DataFrame, min_years: float) -> pd.DataFrame:
    """For each country and A64 industry, how many of its divisions have a series."""
    usable = cov[cov["years_of_observations"] >= min_years]
    have = {(r.country, r.sector) for r in usable.itertuples()}
    rows = []
    for country in EU27:
        for r in a64.itertuples():
            divs = r.ecfin_divisions.split() if r.ecfin_divisions else []
            covered = [d for d in divs if (country, d) in have]
            total = (country, "TOT") in have and r.ecfin_survey == "building"
            rows.append(
                {
                    "country": country,
                    "figaro_code": r.figaro_code,
                    "ecfin_survey": r.ecfin_survey or "none",
                    "divisions_in_survey": len(divs),
                    "divisions_with_series": len(covered),
                    "sector_total_available": bool(total),
                    "status": (
                        "no survey question"
                        if not divs
                        else (
                            "full"
                            if len(covered) == len(divs)
                            else "partial" if covered or total else "missing"
                        )
                    ),
                }
            )
    return pd.DataFrame(rows)


def ecfin_country_summary(cov: pd.DataFrame, a64cov: dict) -> pd.DataFrame:
    rows = []
    for country in EU27:
        c = cov[cov["country"] == country]
        build = c[(c["survey"] == "building") & (c["sector"] == "TOT")]
        indu = c[(c["survey"] == "industry") & (c["sector"] == "TOT")]
        serv = c[(c["survey"] == "services") & (c["sector"] == "TOT")]
        row = {
            "country": country,
            "construction_first": build["first"].iloc[0] if len(build) else "",
            "construction_last": build["last"].iloc[0] if len(build) else "",
            "construction_years": (
                build["years_of_observations"].iloc[0] if len(build) else 0
            ),
            "industry_total_first": indu["first"].iloc[0] if len(indu) else "",
            "services_total_first": serv["first"].iloc[0] if len(serv) else "",
            "services_total_last": serv["last"].iloc[0] if len(serv) else "",
        }
        for years, table in a64cov.items():
            t = table[(table["country"] == country)]
            surveyed = t[t["status"] != "no survey question"]
            row[f"a64_with_series_{years}y"] = int(
                surveyed["status"].isin(["full", "partial"]).sum()
            )
            direct = t[t["figaro_code"].isin(DIRECT_SHOCK_INDUSTRIES)]
            row[f"direct_shock_industries_with_series_{years}y"] = int(
                direct["status"].isin(["full", "partial"]).sum()
            )
        rows.append(row)
    return pd.DataFrame(rows)


# Employment, vacancies ---------------------------------------------------------


def employment_coverage(a64: pd.DataFrame, year: int = 2024):
    path = _processed("nama_10_a64_e")
    df = pd.read_parquet(path)
    df = df[(df["year"] == year) & (df["na_item"] == "EMP_DC")]
    df = df[df["nace_r2"].isin(a64["nama_code"])]
    rows = []
    for country in EU27:
        c = df[df["geo"] == country]
        per = c[(c["unit"] == "THS_PER")].dropna(subset=["obs_value"])
        hrs = c[(c["unit"] == "THS_HW")].dropna(subset=["obs_value"])
        flags = c["obs_flag"].fillna("").str.strip()
        rows.append(
            {
                "country": country,
                "year": year,
                "a64_with_persons": per["nace_r2"].nunique(),
                "a64_with_hours": hrs["nace_r2"].nunique(),
                "construction_persons_available": "F" in set(per["nace_r2"]),
                "construction_hours_available": "F" in set(hrs["nace_r2"]),
                "flagged_estimated": int(flags.str.contains("e").sum()),
                "flagged_provisional": int(flags.str.contains("p").sum()),
                "flagged_confidential": int(flags.str.contains("c").sum()),
            }
        )
    return pd.DataFrame(rows), path


def vacancy_coverage():
    path = _processed("jvs_q_nace2")
    df = pd.read_parquet(path).dropna(subset=["obs_value"])
    df = df[df["s_adj"] == "NSA"]
    rows = []
    for country in EU27:
        c = df[df["geo"] == country]
        f = c[c["nace_r2"] == "F"]
        rows.append(
            {
                "country": country,
                "nace_codes": c["nace_r2"].nunique(),
                "first": c["period"].min() if len(c) else "",
                "last": c["period"].max() if len(c) else "",
                "construction_F_first": f["period"].min() if len(f) else "",
                "construction_F_last": f["period"].max() if len(f) else "",
            }
        )
    return pd.DataFrame(rows), path


# Sweden ------------------------------------------------------------------------


def sweden_join(a64: pd.DataFrame, year: int = 2024):
    scb_path = _processed("scb_yreg54bas")
    nama_path = _processed("nama_10_a64_e")
    scb = pd.read_parquet(scb_path)
    scb = scb[scb["year"] == year]
    nama = pd.read_parquet(nama_path)
    nama = nama[
        (nama["geo"] == "SE")
        & (nama["year"] == year)
        & (nama["unit"] == "THS_PER")
        & (nama["na_item"] == "SAL_DC")
    ]
    rows = []
    for group, g in scb.groupby("group"):
        inds = a64[a64["scb_group"] == group]
        nm = nama[nama["nace_r2"].isin(inds["nama_code"])]
        nm_total = nm["obs_value"].sum() * 1000 if len(nm) else float("nan")
        employees = g["employees"].sum()
        occupations = int((g["employees"] > 0).sum())
        rows.append(
            {
                "scb_group": group,
                "scb_label": g["group_label"].iloc[0],
                "a64_industries": " ".join(inds["figaro_code"]),
                "a64_count": len(inds),
                "scb_employees": int(employees),
                "nama_employees": round(nm_total) if nm_total == nm_total else "",
                "nama_industries_with_value": int(nm["obs_value"].notna().sum()),
                "ratio_scb_to_nama": round(employees / nm_total, 3) if nm_total else "",
                "occupations_with_employees": occupations,
            }
        )
    return pd.DataFrame(rows), [scb_path, nama_path]


# FIGARO ------------------------------------------------------------------------


def figaro_editions() -> pd.DataFrame:
    rows = []
    for path in sorted(PROCESSED_DIR.glob("figaro_*.parquet")):
        prov = read_provenance(path)
        checks = prov.get("checks", {})
        src = prov["sources"][0]
        rows.append(
            {
                "processed_file": path.name,
                "edition": prov.get("edition"),
                "reference_year": prov.get("reference_year"),
                "raw_file": src["file"],
                "sha256": src["sha256"],
                "economies": checks.get("economies"),
                "industries": checks.get("industries"),
                "rows": checks.get("rows"),
                "missing_values": checks.get("missing_values"),
                "max_relative_output_gap": checks.get("output_identity_max_rel_gap"),
            }
        )
    return pd.DataFrame(rows)


# Driver ------------------------------------------------------------------------


def run() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    a64 = concordance.load()
    written, sources = {}, {}

    cov, p = ecfin_coverage()
    sources[p.name] = p
    a64cov = {y: ecfin_a64(cov, a64, y) for y in HISTORY_YEARS}
    summary = ecfin_country_summary(cov, a64cov)
    written["ecfin_labour_series.csv"] = cov
    for y, t in a64cov.items():
        written[f"ecfin_a64_coverage_{y}y.csv"] = t
    written["ecfin_country_summary.csv"] = summary

    emp, p = employment_coverage(a64)
    sources[p.name] = p
    written["employment_coverage_2024.csv"] = emp

    vac, p = vacancy_coverage()
    sources[p.name] = p
    written["vacancy_coverage.csv"] = vac

    swe, ps = sweden_join(a64)
    for p in ps:
        sources[p.name] = p
    written["sweden_scb_group_join_2024.csv"] = swe

    fig = figaro_editions()
    for name in fig["processed_file"]:
        sources[name] = PROCESSED_DIR / name
    written["figaro_editions.csv"] = fig

    for name, table in written.items():
        table.to_csv(OUT_DIR / name, index=False, lineterminator="\n")
    _write_sources(sources)

    no_construction = summary[summary["construction_first"] == ""]["country"].tolist()
    return {
        "tables": sorted(written),
        "stopping_rule_1": {
            "countries_without_construction_labour_series": no_construction,
            "threshold": "more than 9 of 27",
            "fires": len(no_construction) > 9,
        },
    }


def _write_sources(sources: dict[str, Path]) -> None:
    lines = [
        "# Sources of the gate 1 tables",
        "",
        "Every CSV in this folder is computed by `python -m engine gate1` from the "
        "processed files below. Each processed file records the raw files it was "
        "built from; those are listed with their checksums.",
        "",
        "| processed file | raw file | sha256 |",
        "| :--- | :--- | :--- |",
    ]
    for name, path in sorted(sources.items()):
        for src in read_provenance(path).get("sources", []):
            lines.append(f"| {name} | {src['file']} | {src['sha256']} |")
    (OUT_DIR / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
