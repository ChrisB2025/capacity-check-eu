"""End-to-end check of the pipeline on the registered data.

Uses the test-only composition (all spending on construction work), which the
engine refuses outside tests. The assertions are structural and accounting
identities; no figure is printed, saved or compared with an expected value.
Expected-value fixtures (the fixed test set) are built only after the
composition has been confirmed. Skipped when the processed data are absent.
"""

from pathlib import Path

import numpy as np
import pytest

from engine import cdm, pipeline, rating, shock
from engine.params import RunParams
from engine.sources._common import EU27, PROCESSED_DIR

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "composition_engine_check.yaml"
NEEDED = [
    "figaro_2026_y2024.parquet",
    "nama_10_gdp.parquet",
    "nama_10_a64_e.parquet",
    "jvs_q_nace2.parquet",
]

pytestmark = pytest.mark.skipif(
    not all((PROCESSED_DIR / f).exists() for f in NEEDED)
    or not list(PROCESSED_DIR.glob("ecfin_bcs_rel*.parquet")),
    reason="processed data not present; run python -m engine fetch",
)


@pytest.fixture(scope="module")
def result():
    return pipeline.run(RunParams(composition=str(FIXTURE)), allow_unconfirmed=True)


def test_refuses_unconfirmed_composition():
    with pytest.raises(shock.CompositionNotConfirmed):
        pipeline.run(RunParams(composition=str(FIXTURE)))


def test_table_shapes(result):
    t = result.tables
    assert len(t["countries"]) == 27
    assert len(t["lines"]) == 27 * 64
    assert len(t["industry_detail"]) == 27 * 64
    assert set(t["countries"]["country"]) == set(EU27)


def test_direct_demand_adds_up_to_the_shock(result):
    dd = result.tables["direct_demand"]
    by_country = dd.groupby("country")["meur"].sum()
    shock_meur = result.tables["countries"].set_index("country")["shock_meur"]
    assert np.allclose(by_country.sort_index(), shock_meur.sort_index())
    assert np.allclose(dd["home"] + dd["rest_eu"] + dd["non_eu"], 1.0)


def test_required_output_at_least_the_shock(result):
    c = result.tables["countries"]
    assert (c["required_output_meur"] >= c["shock_meur"] * (1 - 1e-9)).all()
    shares = (
        c["required_home_share"]
        + c["required_rest_eu_share"]
        + c["required_non_eu_share"]
    )
    assert np.allclose(shares, 1.0)


def test_industry_detail_sums_to_country_total(result):
    d = result.tables["industry_detail"]
    tot = (
        d.groupby("country")[
            ["required_home_meur", "required_rest_eu_meur", "required_non_eu_meur"]
        ]
        .sum()
        .sum(axis=1)
    )
    c = result.tables["countries"].set_index("country")["required_output_meur"]
    assert np.allclose(tot.sort_index(), c.sort_index())


def test_ratings_and_shares_are_valid(result):
    lines = result.tables["lines"]
    allowed = {rating.CLEAR, rating.TIGHT, rating.BINDING, rating.NO_RATING}
    assert set(lines["rating"]) <= allowed
    assert (lines["extra_persons_all"].fillna(0) >= 0).all()
    h = result.tables["countries"]["headline_tight_or_binding_share"]
    assert ((h >= 0) & (h <= 1)).all()


def test_run_id_is_deterministic(result):
    again = pipeline.run(RunParams(composition=str(FIXTURE)), allow_unconfirmed=True)
    assert again.run_id == result.run_id


def test_cdm_tables(result):
    out = cdm.write(result)
    assert len(out["Region"]) == 27
    assert len(out["RealResourceConstraint"]) == 27 * 64
    for name, df in out.items():
        assert list(df.columns) == cdm.FIELDS[name]
    rrc = out["RealResourceConstraint"]
    assert rrc["constraint_id"].is_unique
    assert set(rrc["unit_of_measure"]) == {"PERSONS"}
