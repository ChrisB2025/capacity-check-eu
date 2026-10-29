"""Step 8, the Swedish occupational split, on the real data.

Skipped when the processed data are absent.
"""

import numpy as np
import pytest

from engine import pipeline, sweden
from engine.params import RunParams
from engine.sources._common import PROCESSED_DIR

HAVE_DATA = all(
    (PROCESSED_DIR / f).exists()
    for f in (
        "figaro_2026_y2024.parquet",
        "scb_yreg54bas.parquet",
        "scb_yreg52bas.parquet",
        "af_yrkesbarometer.parquet",
        "konj_barboam.parquet",
    )
)
pytestmark = pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")


@pytest.fixture(scope="module")
def result():
    return pipeline.run(RunParams(), allow_unconfirmed=True)


@pytest.fixture(scope="module")
def tables(result):
    return sweden.run(result)


def test_occupations_add_up_to_swedish_extra_persons(result, tables):
    occ = tables["sweden_occupations"]
    assert occ["extra_persons"].sum() == pytest.approx(
        sweden.extra_persons(result).sum(), rel=1e-9
    )


def test_shares_sum_to_one(tables):
    occ = tables["sweden_occupations"]
    assert occ["share_of_swedish_extra"].sum() == pytest.approx(1.0)
    assert occ["share_of_known_extra"].sum() == pytest.approx(1.0)


def test_unknown_occupation_flagged(tables):
    occ = tables["sweden_occupations"]
    unknown = occ[~occ["known_occupation"]]
    assert list(unknown["ssyk"]) == ["0002"]
    assert unknown["share_of_known_extra"].isna().all()


def test_no_negative_values(tables):
    for name, df in tables.items():
        nums = df.select_dtypes(include=[np.number])
        assert (nums.fillna(0) >= 0).all().all(), name


def test_forecasts_take_the_largest_known_occupations(tables):
    occ = tables["sweden_occupations"]
    fc = tables["sweden_forecasts"]
    assert len(fc) == sweden.TOP_N
    known = occ[occ["known_occupation"]]["ssyk"]
    assert list(fc["ssyk"]) == list(known[: sweden.TOP_N])
    assert fc["ela_shortage_sweden"].isna().all()


def test_konj_not_marked_publishable(tables):
    k = tables["sweden_konj"]
    konj = k[k["source"] == "Konjunkturinstitutet"]
    assert len(konj) == 4
    assert not konj["publishable"].any()


def test_sources_have_checksums():
    for s in sweden.sources():
        assert len(s["sha256"]) == 64
