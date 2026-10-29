"""Step 8. Swedish occupational split.

Splits the extra jobs on Swedish lines into 4-digit SSYK 2012 occupations
using Statistics Sweden table YREG54BAS, and sets the largest occupations
beside Arbetsförmedlingen's Yrkesbarometer, the fields of education of
their workers (YREG52BAS), and Konjunkturinstitutet's construction survey as
a cross-check of the DG ECFIN slack for Sweden.

``run(result)`` takes a ``pipeline.run`` result and returns four tables:

* ``sweden_occupations``: extra persons by occupation
* ``sweden_forecasts``: the largest occupations with the Yrkesbarometer
  assessment, and the ELA column (empty, see below)
* ``sweden_education``: the largest occupations by their workers' main field
  of education, and how many people with that field work elsewhere
* ``sweden_konj``: construction labour shortage readings, Konjunkturinstitutet
  beside DG ECFIN, each placed in its own history

Sweden is a demonstration, not a validation: no Swedish programme with
documented bottlenecks exists to test against.

The ELA 2025 report gives no shortage status by occupation for Sweden (its
occupation list by country is not published in the report), so the ELA
column is left empty rather than filled from the EU-wide tables.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from engine import concordance, slack
from engine.sources import scb
from engine.sources._common import PROCESSED_DIR, RAW_DIR, read_provenance

COUNTRY = "SE"
TOP_N = 25
YREG54 = PROCESSED_DIR / "scb_yreg54bas.parquet"
YREG52 = PROCESSED_DIR / "scb_yreg52bas.parquet"
YRKESBAROMETER = PROCESSED_DIR / "af_yrkesbarometer.parquet"
KONJ = PROCESSED_DIR / "konj_barboam.parquet"
ELA_PDF = "ela-eures-shortages_2025-report_20261029.pdf"

KONJ_LABOUR = "1084"
KONJ_NOT_ADJUSTED = "O"
KONJ_SECTORS = {"BBYG": "TOT", "B41000": "41", "B42000": "42", "B43000": "43"}
# Decision 4 of gate 1 is open: Konjunkturinstitutet states no reuse licence,
# so its values are for internal cross-checking and are not published.
KONJ_PUBLISHABLE = False
UNKNOWN_EDUCATION = "9"

# Yrkesbarometer categories, in English.
JOB_PROSPECTS = {"stora": "large", "medelstora": "medium", "små": "small"}
RECRUITMENT = {
    "brist": "shortage",
    "balans": "balance",
    "överskott": "surplus",
    "paradox": "paradox",
}
OUTLOOK = {"öka": "increase", "vara oförändrad": "unchanged", "minska": "decrease"}


def sources() -> list[dict]:
    """Every file behind the Swedish tables, with its checksum."""
    out = []
    files = [YREG54, YREG52, YRKESBAROMETER, KONJ]
    files.append(sorted(PROCESSED_DIR.glob("ecfin_bcs_rel*.parquet"))[-1])
    for f in files:
        for s in read_provenance(f).get("sources", []):
            out.append(
                {
                    "dataset": s.get("dataset", f.stem),
                    "edition": s.get("edition", ""),
                    "file": s["file"],
                    "sha256": s["sha256"],
                }
            )
    ela = RAW_DIR / ELA_PDF
    if ela.exists():
        out.append(
            {
                "dataset": "ela-eures-shortages",
                "edition": "2025-report",
                "file": ela.name,
                "sha256": hashlib.sha256(ela.read_bytes()).hexdigest(),
            }
        )
    return out


def extra_persons(result) -> pd.Series:
    """Extra persons on each Swedish line, on the run's application basis."""
    lines = result.tables["lines"]
    se = lines[lines["economy"] == COUNTRY].set_index("industry")
    col = (
        "extra_persons_all"
        if result.params.application == "simultaneous"
        else "extra_persons_own"
    )
    return se[col].astype(float)


def _register(path=YREG54) -> tuple[pd.DataFrame, int]:
    df = pd.read_parquet(path)
    year = int(df["year"].max())
    return df[df["year"] == year].copy(), year


def occupations(result) -> pd.DataFrame:
    extra = extra_persons(result)
    groups = concordance.load().set_index("figaro_code")["scb_group"]
    reg, year = _register()
    reg["employees"] = reg["employees"].astype(float)
    mix = reg[reg["group"] != scb.UNKNOWN_INDUSTRY].copy()
    totals = mix.groupby("group")["employees"].transform("sum")
    mix["mix"] = np.where(totals > 0, mix["employees"] / totals, 0.0)

    by_group = extra.groupby(groups.reindex(extra.index)).sum()
    mix["extra"] = mix["group"].map(by_group).fillna(0.0) * mix["mix"]

    occ = mix.groupby(["ssyk", "ssyk_label"], as_index=False)["extra"].sum()
    largest = (
        mix.sort_values("extra", ascending=False)
        .drop_duplicates("ssyk")
        .set_index("ssyk")
    )
    occ["largest_source_group"] = occ["ssyk"].map(largest["group"])
    occ["largest_source_group_label"] = occ["ssyk"].map(largest["group_label"])
    occ["largest_source_share"] = np.where(
        occ["extra"] > 0,
        occ["ssyk"].map(largest["extra"]) / occ["extra"],
        np.nan,
    )
    emp = reg.groupby("ssyk")["employees"].sum()
    occ["employees"] = occ["ssyk"].map(emp)
    occ["known_occupation"] = occ["ssyk"] != scb.UNKNOWN_OCCUPATION
    total = occ["extra"].sum()
    known = occ.loc[occ["known_occupation"], "extra"].sum()
    occ["share_of_swedish_extra"] = occ["extra"] / total if total else 0.0
    occ["share_of_known_extra"] = np.where(
        occ["known_occupation"], occ["extra"] / known if known else 0.0, np.nan
    )
    occ["extra_share_of_occupation_employees"] = np.where(
        occ["employees"] > 0, occ["extra"] / occ["employees"], np.nan
    )
    occ["register_year"] = year
    occ = occ.rename(columns={"ssyk_label": "occupation", "extra": "extra_persons"})
    occ = occ.sort_values(
        ["known_occupation", "extra_persons"], ascending=[False, False]
    )
    cols = [
        "ssyk",
        "occupation",
        "known_occupation",
        "extra_persons",
        "share_of_swedish_extra",
        "share_of_known_extra",
        "employees",
        "register_year",
        "extra_share_of_occupation_employees",
        "largest_source_group",
        "largest_source_group_label",
        "largest_source_share",
    ]
    return occ[cols].reset_index(drop=True)


def top(occ: pd.DataFrame, n: int = TOP_N) -> pd.DataFrame:
    return occ[occ["known_occupation"]].head(n)


def _join(values: pd.Series) -> str | None:
    seen = [v for v in dict.fromkeys(values.dropna()) if v != ""]
    return "; ".join(seen) if seen else None


def forecasts(occ: pd.DataFrame) -> pd.DataFrame:
    yb = pd.read_parquet(YRKESBAROMETER)
    nat = yb[yb["lan"] == "00"].copy()
    nat["job_prospects"] = nat["jobbmojligheter"].map(JOB_PROSPECTS)
    nat["recruitment"] = nat["rekryteringssituation"].map(RECRUITMENT)
    nat["outlook_5y"] = nat["prognos"].map(OUTLOOK)
    agg = nat.groupby("ssyk").agg(
        af_occupations=("yb_yrke", _join),
        af_job_prospects=("job_prospects", _join),
        af_recruitment=("recruitment", _join),
        af_outlook_5y=("outlook_5y", _join),
        af_round=("omgang", _join),
        af_part_of_ssyk=("del_av_ssyk", "max"),
    )
    t = top(occ)[["ssyk", "occupation", "extra_persons", "share_of_swedish_extra",
                  "employees", "extra_share_of_occupation_employees"]]  # fmt: skip
    t = t.merge(agg, left_on="ssyk", right_index=True, how="left")
    t["af_part_of_ssyk"] = t["af_part_of_ssyk"].map(
        {1: True, 0: False}, na_action="ignore"
    )
    t["af_covered"] = t["af_occupations"].notna()
    t["ela_shortage_sweden"] = None
    t["ela_note"] = (
        "The ELA 2025 report publishes no shortage status by occupation for "
        "Sweden; its country lists are not in the report."
    )
    return t.reset_index(drop=True)


def education(occ: pd.DataFrame) -> pd.DataFrame:
    edu, year = _register(YREG52)
    edu["employees"] = edu["employees"].astype(float)
    known = edu[edu["group"] != UNKNOWN_EDUCATION]
    by_field = known.groupby("group")["employees"].sum()
    labels = known.drop_duplicates("group").set_index("group")["group_label"]
    rows = []
    for r in top(occ).itertuples():
        own = edu[edu["ssyk"] == r.ssyk]
        total = own["employees"].sum()
        own_known = own[own["group"] != UNKNOWN_EDUCATION]
        if own_known.empty or own_known["employees"].sum() == 0:
            continue
        main = own_known.sort_values("employees", ascending=False).iloc[0]
        field_total = by_field[main["group"]]
        rows.append(
            {
                "ssyk": r.ssyk,
                "occupation": r.occupation,
                "extra_persons": r.extra_persons,
                "employees": total,
                "main_field": main["group"],
                "main_field_label": labels[main["group"]].strip(),
                "main_field_share": main["employees"] / total if total else np.nan,
                "unknown_field_share": (
                    own.loc[own["group"] == UNKNOWN_EDUCATION, "employees"].sum()
                    / total
                    if total
                    else np.nan
                ),
                "field_employed_all_occupations": field_total,
                "field_employed_outside_occupation": field_total - main["employees"],
                "register_year": year,
            }
        )
    return pd.DataFrame(rows)


def _monthly(values: pd.Series, periods: pd.Series) -> pd.Series:
    idx = pd.PeriodIndex(periods.str.replace("M", "-", regex=False), freq="M")
    return pd.Series(values.to_numpy(dtype=float), index=idx).sort_index()


def konj(result) -> pd.DataFrame:
    p = result.params
    t = p.thresholds
    window = 3 * p.slack_window_quarters
    k = pd.read_parquet(KONJ)
    k = k[(k["question"] == KONJ_LABOUR) & (k["series"] == KONJ_NOT_ADJUSTED)]
    k = k.dropna(subset=["value"])
    lab, ecfin_file = slack._ecfin_frame(adjusted=False)
    lab = lab[(lab["country"] == COUNTRY) & (lab["survey"] == "building")]

    rows = []
    for code, sector in KONJ_SECTORS.items():
        kg = k[k["sector"] == code]
        ks = _monthly(kg["value"], kg["period"])
        eg = lab[lab["sector"] == sector]
        es = _monthly(eg["value"], eg["period"])
        overlap = es[es.index >= ks.index.min()] if not ks.empty else es.iloc[:0]
        both = pd.concat([ks, es], axis=1, join="inner").dropna()
        for source, s, note in (
            ("Konjunkturinstitutet", ks, "Barboam.px question 1084, not adjusted"),
            ("DG ECFIN", es, f"{ecfin_file}, full history"),
            ("DG ECFIN", overlap, f"{ecfin_file}, from Konjunkturinstitutet's start"),
        ):
            pos = slack.position(
                s,
                window,
                p.slack_min_years,
                t.slack_median_quantile,
                t.slack_top_quantile,
                per_year=12,
            )
            rows.append(
                {
                    "sector": sector,
                    "source": source,
                    "basis": note,
                    "first": pos.first,
                    "last": pos.last,
                    "years": pos.years,
                    "current_12m_mean": pos.current,
                    "percentile": pos.percentile,
                    "median": pos.median,
                    "top_quartile": pos.top_quartile,
                    "slack_class": pos.slack_class,
                    "note": pos.note,
                    "months_in_common": len(both),
                    "correlation_in_common": (
                        float(both.iloc[:, 0].corr(both.iloc[:, 1]))
                        if len(both) > 2
                        else np.nan
                    ),
                    "publishable": source != "Konjunkturinstitutet" or KONJ_PUBLISHABLE,
                }
            )
    return pd.DataFrame(rows)


def run(result) -> dict[str, pd.DataFrame]:
    occ = occupations(result)
    return {
        "sweden_occupations": occ,
        "sweden_forecasts": forecasts(occ),
        "sweden_education": education(occ),
        "sweden_konj": konj(result),
    }
