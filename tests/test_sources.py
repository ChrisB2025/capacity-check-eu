"""Unit tests for source parsers and helpers.

The inputs here are small synthetic structures that exercise parsing logic
only. They are not data and never feed a result.
"""

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pytest

from engine import concordance
from engine.sources import _common, ecfin, figaro, pxweb

# Concordance -------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, divs",
    [
        ("C10-12", [10, 11, 12]),
        ("C31_32", [31, 32]),
        ("F", [41, 42, 43]),
        ("B", [5, 6, 7, 8, 9]),
        ("M71", [71]),
        ("N80-82", [80, 81, 82]),
    ],
)
def test_divisions(code, divs):
    assert concordance.divisions(code) == divs


@pytest.mark.parametrize(
    "code, nama",
    [("C10-12", "C10-C12"), ("J59_60", "J59_J60"), ("F", "F"), ("M71", "M71")],
)
def test_nama_code(code, nama):
    assert concordance.nama_code(code) == nama


def test_committed_concordance_matches_rules():
    a64 = concordance.load()
    assert a64["figaro_code"].tolist() == list(concordance.FIGARO_A64)
    for r in a64.itertuples():
        assert r.nama_code == concordance.nama_code(r.figaro_code)
        survey, covered = concordance.ecfin_survey(concordance.divisions(r.figaro_code))
        assert r.ecfin_survey == survey
        assert r.ecfin_divisions == " ".join(f"{d:02d}" for d in covered)
        assert r.label


# ECFIN -------------------------------------------------------------------------


def test_period_parsing():
    assert ecfin._period("1985-Q1", "Q") == "1985Q1"
    assert ecfin._period(dt.datetime(2026, 10, 31), "M") == "2026-10"
    assert ecfin._period(46326, "M") == "2026-10"
    assert ecfin._period(None, "M") is None


def test_parse_sheet_long_format():
    sheet = pd.DataFrame(
        [
            ["41", "", "BUIL.SE.41.2.F4.M", "BUIL.SE.41.2.F1.M", "not a series"],
            [dt.datetime(2026, 9, 30), None, 10.0, "NA", 1],
            [dt.datetime(2026, 10, 31), None, 12.5, 3.0, 2],
        ],
        dtype=object,
    )
    out = ecfin.parse_sheet(sheet, "building_subsectors_nsa_m_nace2.xlsx", False)
    assert set(out["series"]) == {"BUIL.SE.41.2.F4.M", "BUIL.SE.41.2.F1.M"}
    f4 = out[out["answer"] == "F4"].sort_values("period")
    assert f4["period"].tolist() == ["2026-09", "2026-10"]
    assert f4["survey"].iloc[0] == "building"
    assert len(out[out["answer"] == "F1"]) == 1  # the NA cell is dropped


def test_labour_answers_found_by_label():
    cb = pd.DataFrame(
        [
            ("building_total_nsa_nace2.xlsx", "Answers", "F3",
             "Weather conditions (% n.s.a. - monthly question 2)"),
            ("building_total_nsa_nace2.xlsx", "Answers", "F4",
             "Shortage of labour force (% n.s.a. - monthly question 2)"),
            ("industry_total_nsa_nace2.xlsx", "Answers", "F3",
             "Labour (% n.s.a - quarterly question 8)"),
        ],
        columns=["workbook", "section", "code", "label"],
    )  # fmt: skip
    assert ecfin.labour_answers(cb) == {
        "building": ("2", "F4"),
        "industry": ("8", "F3"),
    }


# FIGARO ------------------------------------------------------------------------


def _tiny_table(gap=0.0):
    """Two economies, two industries, one final demand column, balanced."""
    rows = []
    inds = ["X", "Y"]
    for co in ("AA", "BB"):
        for ia in inds:
            for cd in ("AA", "BB"):
                for iu in [*inds, "P3_S14"]:
                    rows.append((co, ia, cd, iu, 1.0))
    # each industry column gets 4 intermediate inputs; rows sum to 6, so
    # value added of 2 per column balances the identity
    for cd in ("AA", "BB"):
        for iu in inds:
            rows.append(("DOM", "B2A3G", cd, iu, 2.0 + gap))
    df = pd.DataFrame(rows, columns=["c_orig", "ind_ava", "c_dest", "ind_use", "value"])
    df["flag"] = ""
    for col in ("c_orig", "ind_ava", "c_dest", "ind_use", "flag"):
        df[col] = df[col].astype("category")
    return df


def test_figaro_identity_holds(monkeypatch):
    monkeypatch.setattr(figaro, "N_INDUSTRIES", 2)
    monkeypatch.setattr(figaro, "FINAL_DEMAND", ("P3_S14",))
    checks = figaro.validate(_tiny_table())
    assert checks["economies"] == 2
    assert checks["output_identity_max_abs_gap_meur"] == 0


def test_figaro_identity_detects_gap(monkeypatch):
    monkeypatch.setattr(figaro, "N_INDUSTRIES", 2)
    monkeypatch.setattr(figaro, "FINAL_DEMAND", ("P3_S14",))
    checks = figaro.validate(_tiny_table(gap=0.5))
    assert checks["output_identity_max_abs_gap_meur"] == pytest.approx(0.5)


def test_dataflow_for_year():
    assert figaro.dataflow_for(2010) == "naio_10_fcp_ii1"
    assert figaro.dataflow_for(2024) == "naio_10_fcp_ii4"
    with pytest.raises(_common.SourceError):
        figaro.dataflow_for(2009)


# PxWeb -------------------------------------------------------------------------


def test_read_jsonstat2(tmp_path: Path):
    ds = {
        "id": ["Yrke", "Tid"],
        "size": [2, 2],
        "dimension": {
            "Yrke": {"category": {"index": {"7111": 0, "7112": 1},
                                  "label": {"7111": "Snickare", "7112": "Murare"}}},
            "Tid": {"category": {"index": {"2023": 0, "2024": 1}}},
        },
        "value": [1, 2, 3, None],
    }  # fmt: skip
    p = tmp_path / "x.json"
    p.write_text(json.dumps(ds), encoding="utf-8")
    df = pxweb.read_jsonstat2(p)
    assert df.loc[(df.Yrke == "7112") & (df.Tid == "2023"), "value"].item() == 3
    assert df.loc[df.Yrke == "7111", "Yrke_label"].iloc[0] == "Snickare"
    assert df["value"].isna().sum() == 1


# Register ----------------------------------------------------------------------


def test_record_is_idempotent(tmp_path: Path, monkeypatch):
    reg = tmp_path / "register.md"
    reg.write_text("| key |\n| :--- |\n", encoding="utf-8")
    sums = tmp_path / "checksums.txt"
    monkeypatch.setattr(_common, "REGISTER_MD", reg)
    monkeypatch.setattr(_common, "CHECKSUMS", sums)
    f = tmp_path / "file.bin"
    f.write_bytes(b"abc")
    raw = _common.RawFile("k", "ds", "ed", "url", "2026-10-29", f,
                          _common.sha256_file(f))  # fmt: skip
    _common.record(raw, "pub", "lic")
    _common.record(raw, "pub", "lic")
    assert reg.read_text(encoding="utf-8").count(raw.sha256) == 1
    assert sums.read_text(encoding="utf-8").count(raw.sha256) == 1


def test_parquet_carries_provenance(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(_common, "PROCESSED_DIR", tmp_path)
    f = tmp_path / "raw.bin"
    f.write_bytes(b"abc")
    raw = _common.RawFile("k", "ds", "ed", "url", "2026-10-29", f,
                          _common.sha256_file(f))  # fmt: skip
    out = _common.write_parquet(pd.DataFrame({"a": [1]}), "t", [raw], edition="x")
    prov = _common.read_provenance(out)
    assert prov["sources"][0]["sha256"] == raw.sha256
    assert prov["edition"] == "x"
