"""The fixed test set: rerun each case and compare with its stored outputs.

Skipped when the processed data or a case's fixtures are absent. A failure
means results changed: either a bug, or an intended change that needs the
fixtures regenerated with ``python -m engine testset`` and explained.
"""

import json

import pandas as pd
import pytest

from engine import testset
from engine.sources._common import PROCESSED_DIR

HAVE_DATA = (PROCESSED_DIR / "figaro_2026_y2024.parquet").exists()


@pytest.mark.parametrize("name", list(testset.CASES))
def test_case_reproduces(name):
    manifest = testset.FIXTURE_DIR / f"{name}_manifest.json"
    if not HAVE_DATA or not manifest.exists():
        pytest.skip("data or fixtures not present")
    expected = json.loads(manifest.read_text(encoding="utf-8"))
    res = testset.run_case(name, allow_unconfirmed=expected["provisional"])
    assert (
        res.run_id == expected["run_id"]
    ), "inputs changed: data, params or composition"
    countries, lines = testset.outputs(res)
    for got, suffix in ((countries, "countries"), (lines, "lines")):
        want = pd.read_csv(testset.FIXTURE_DIR / f"{name}_{suffix}.csv")
        got = got.reset_index(drop=True)
        pd.testing.assert_frame_equal(
            got, want, check_dtype=False, rtol=1e-9, atol=1e-9
        )
