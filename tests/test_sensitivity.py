"""Threshold sensitivity and the new engine tables (review of 18 Nov 2026)."""

import numpy as np
import pandas as pd
import pytest

from engine import rating, results, sensitivity, testset
from engine.params import Thresholds
from tests.test_fixed_set import HAVE_DATA


def _frame():
    return pd.DataFrame(
        {
            "economy": ["AT", "AT", "BE", "BE"],
            "industry": ["F", "C28", "F", "C28"],
            "pressure": [0.06, 0.025, 0.015, np.nan],
            "slack_class": ["high", "low", "low", "high"],
            "persons_basis": ["A64", "A64", "A64", "A64"],
            "extra_persons_all": [100.0, 50.0, 30.0, 20.0],
        }
    )


def _lines():
    f = _frame()
    return f.assign(rating=sensitivity.rerate(f, Thresholds()))


def test_rerate_follows_the_rule():
    got = sensitivity.rerate(_lines(), Thresholds())
    assert list(got) == [rating.BINDING, rating.TIGHT, rating.CLEAR, rating.NO_RATING]
    low = sensitivity.rerate(_lines(), Thresholds(pressure_low=0.01))
    assert low.iloc[2] == rating.TIGHT


def test_jobs_share_counts_tight_and_binding():
    lines = _lines()
    share = sensitivity._jobs_share(lines, sensitivity.rerate(lines, Thresholds()))
    assert share == pytest.approx(150 / 200)


def test_pressure_grid_has_one_current_row():
    grid = sensitivity.pressure_grid(_lines(), Thresholds())
    assert grid["current"].sum() == 1
    cur = grid[grid["current"]].iloc[0]
    assert cur["ratings_changed"] == 0
    assert (grid["pressure_low"] < grid["pressure_high"]).all()


def test_pressure_grid_includes_an_unusual_current_setting():
    t = Thresholds(pressure_low=0.025, pressure_high=0.06)
    grid = sensitivity.pressure_grid(_lines(), t)
    assert grid["current"].sum() == 1
    assert grid.iloc[0]["pressure_low"] == 0.025


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
def test_rerating_matches_a_full_rerun():
    """Re-rating the base run at 1% and 3% gives the thresholds_test run."""
    base = testset.run_case("base", allow_unconfirmed=True)
    t = Thresholds(pressure_low=0.01, pressure_high=0.03)
    got = base.tables["lines"][["economy", "industry"]].assign(
        rating=sensitivity.rerate(base.tables["lines"], t).to_numpy()
    )
    want = pd.read_csv(testset.FIXTURE_DIR / "thresholds_test_lines.csv")
    m = want.merge(got, on=["economy", "industry"], suffixes=("_want", "_got"))
    assert len(m) == len(want)
    assert (m["rating_want"] == m["rating_got"]).all()


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
def test_sensitivity_and_summary_tables():
    base = testset.run_case("base", allow_unconfirmed=True)
    table = sensitivity.table(base)
    assert set(table["kind"]) == {"pressure", "slack"}
    current = table[table["current"]]
    assert len(current) == 2 and (current["ratings_changed"] == 0).all()
    ov = results.overview(base).iloc[0]
    assert current["jobs_tight_or_binding_share"].iloc[0] == pytest.approx(
        ov["headline_jobs_weighted"]
    )
    s = results.executive_summary(base).iloc[0]
    assert s["headline_jobs_weighted"] == pytest.approx(ov["headline_jobs_weighted"])
    assert s["countries"] == 27
    assert 0 <= s["construction_tight_or_binding"] <= s["construction_rated"] <= 27


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
def test_allocation_maps_every_line_to_nace():
    base = testset.run_case("base", allow_unconfirmed=True)
    a = results.allocation(base)
    assert a["share"].sum() == pytest.approx(1.0)
    total = base.tables["countries"]["shock_meur"].sum()
    assert a["meur"].sum() == pytest.approx(total)
    f = a.set_index("code").loc["F"]
    assert f["nace_divisions"] == "41, 42, 43"
    for k in ("home_share", "rest_eu_share", "non_eu_share"):
        assert a[k].between(0, 1).all()
