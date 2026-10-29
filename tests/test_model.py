"""Unit tests for the model steps, on small synthetic inputs with known answers.

These inputs exercise the arithmetic only. They are not data and never feed
a result.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine import cdm, io_model, rating, robustness, shock, slack
from engine.params import RunParams, Thresholds

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


# Step 2: Leontief -------------------------------------------------------------


def test_leontief_reproduces_output():
    Z = np.array([[10.0, 20.0], [30.0, 40.0]])
    x = np.array([100.0, 200.0])
    f = x - Z.sum(axis=1)
    L = io_model.leontief_inverse(Z, x)
    assert np.allclose(L @ f, x)
    A = io_model.technical_coefficients(Z, x)
    assert np.allclose(A, [[0.1, 0.1], [0.3, 0.2]])


def test_zero_output_column_is_zero():
    Z = np.array([[1.0, 0.0], [2.0, 0.0]])
    A = io_model.technical_coefficients(Z, np.array([10.0, 0.0]))
    assert A[:, 1].tolist() == [0.0, 0.0]


# Step 1: composition and direct demand ----------------------------------------


def _comp(lines, status="confirmed"):
    return shock.Composition("t", status, tuple(shock.Line(c, s, c) for c, s in lines))


def test_composition_shares_must_sum_to_one():
    with pytest.raises(ValueError, match="sum"):
        _comp([("F", 0.6), ("M71", 0.3)]).validate()


def test_composition_rejects_unknown_codes():
    with pytest.raises(ValueError, match="unknown"):
        _comp([("XYZ", 1.0)]).validate()


def test_unconfirmed_composition_cannot_run():
    with pytest.raises(shock.CompositionNotConfirmed):
        _comp([("F", 1.0)], status="proposed").require_confirmed()


def test_fixture_composition_is_test_only():
    comp = shock.load_composition(FIXTURES / "composition_engine_check.yaml")
    with pytest.raises(shock.CompositionNotConfirmed):
        comp.require_confirmed()


def _tiny_model():
    """Two economies (AA, BB) and the 64 industries; only F flows are non-zero."""
    from engine import concordance

    inds = concordance.load()["figaro_code"].tolist()
    econs = ["AA", "BB"]
    n = len(econs) * len(inds)
    cols = [("AA", "P51G"), ("AA", "P3_S14"), ("BB", "P51G")]
    F = np.zeros((n, len(cols)))
    f = inds.index("F")
    F[0 * len(inds) + f, 0] = 90.0  # AA buys F from AA for investment
    F[1 * len(inds) + f, 0] = 10.0  # and from BB
    return io_model.Model(
        "t", 2024, econs, inds, np.eye(n), np.ones(n), F, cols, "none", "none"
    )


def test_direct_demand_follows_investment_origin_pattern():
    m = _tiny_model()
    dd = shock.direct_demand(
        m, _comp([("F", 1.0)]), "AA", gdp=1000.0, shock_pct=1.0, eu=("AA", "BB")
    )
    assert dd.amount_meur == pytest.approx(10.0)
    assert dd.y[m.position("AA", "F")] == pytest.approx(9.0)
    assert dd.y[m.position("BB", "F")] == pytest.approx(1.0)
    row = dd.by_product.iloc[0]
    assert row["home"] == pytest.approx(0.9)
    assert row["rest_eu"] == pytest.approx(0.1)
    assert row["origin_basis"] == "P51G"


def test_origin_falls_back_to_domestic():
    m = _tiny_model()
    shares, basis = shock.origin_shares(m, "BB", "M71", "P51G")
    assert basis == "assumed domestic"
    assert shares.tolist() == [0.0, 1.0]


# Step 5: slack ----------------------------------------------------------------


def _quarters(values, start="2000Q1"):
    idx = pd.period_range(start, periods=len(values), freq="Q")
    return pd.Series(values, index=idx, dtype=float)


def test_slack_position_top_of_history_is_high():
    p = slack.position(_quarters(range(1, 41)), window=4, min_years=5)
    assert p.current == pytest.approx(38.5)
    assert p.percentile == pytest.approx(1.0)
    assert p.slack_class == slack.HIGH


def test_slack_position_bottom_is_low():
    p = slack.position(_quarters(range(40, 0, -1)), window=4, min_years=5)
    assert p.slack_class == slack.LOW


def test_slack_needs_enough_history():
    p = slack.position(_quarters(range(1, 13)), window=4, min_years=5)
    assert p.slack_class is None
    assert "below" in p.note


def test_slack_missing_series():
    p = slack.position(pd.Series(dtype=float), window=4, min_years=5)
    assert p.slack_class is None and p.note == "no series"


# Step 6: rating ---------------------------------------------------------------


@pytest.mark.parametrize(
    "pressure, cls, expected",
    [
        (0.01, slack.LOW, rating.CLEAR),
        (0.03, slack.LOW, rating.TIGHT),
        (0.01, slack.ELEVATED, rating.TIGHT),
        (0.06, slack.ELEVATED, rating.TIGHT),
        (0.06, slack.HIGH, rating.BINDING),
        (0.05, slack.HIGH, rating.TIGHT),  # binding needs pressure above 5%
        (0.06, None, rating.NO_RATING),
        (float("nan"), slack.LOW, rating.NO_RATING),
    ],
)
def test_rating_rule(pressure, cls, expected):
    assert rating.rate(pressure, cls, Thresholds()) == expected


def test_thresholds_are_parameters():
    t = Thresholds(pressure_low=0.005)
    assert rating.rate(0.01, slack.LOW, t) == rating.TIGHT


def test_quality_grades():
    assert rating.quality({"a": 0.05}, [])[0] == "good"
    assert rating.quality({"a": 0.05}, ["note"])[0] == "limited"
    assert rating.quality({"a": 0.2}, [])[0] == "limited"
    assert rating.quality({"a": 0.5}, [])[0] == "poor"


def test_params_validate():
    with pytest.raises(ValueError):
        RunParams(shock_pct=3.0)
    assert RunParams().digest() == RunParams().digest()
    assert RunParams().digest() != RunParams(shock_pct=2.0).digest()


# Step 9: robustness -----------------------------------------------------------


def test_compare_ratings_excludes_unrated():
    base = pd.DataFrame(
        {
            "economy": ["A"] * 4,
            "industry": list("abcd"),
            "rating": ["clear", "tight", "no rating", "binding"],
        }
    )
    alt = pd.DataFrame(
        {
            "economy": ["A"] * 4,
            "industry": list("abcd"),
            "rating": ["clear", "binding", "clear", "binding"],
        }
    )
    out = robustness.edition_test(base, alt)
    assert out["lines_rated_in_both"] == 3
    assert out["ratings_changed"] == 1
    assert out["share_changed"] == pytest.approx(1 / 3)
    assert out["stopping_rule_fires"] is True


# Canonical data model -----------------------------------------------------------


def _baseline_fields(entity: str) -> list[str]:
    """Attribute names of ``entity`` as written in the frozen baseline document."""
    lines = (
        (ROOT / "docs" / "cdm-v1.6.2-baseline.md")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    start = next(
        k for k, ln in enumerate(lines) if re.match(rf"### [\d.]+ {entity}\b", ln)
    )
    table = []
    for ln in lines[start + 1 :]:
        if ln.startswith("### "):
            break
        if ln.startswith("|"):
            table.append(ln)
        elif table:
            break
    if entity == "UnitOfMeasure":  # a reference table: its header is the fields
        return [c.strip() for c in table[0].strip("|").split("|")]
    return [ln.split("|")[1].strip() for ln in table[2:]]


@pytest.mark.parametrize("entity", list(cdm.FIELDS))
def test_cdm_fields_match_frozen_baseline(entity):
    assert cdm.FIELDS[entity] == _baseline_fields(entity)


def test_economic_activity_has_64_rows():
    ea = cdm.economic_activity()
    assert len(ea) == 64
    assert list(ea.columns) == cdm.FIELDS["EconomicActivity"]
    assert ea["activity_id"].is_unique
