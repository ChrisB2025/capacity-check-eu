"""The web app shows the engine's numbers unchanged (Phase 4 gate).

Each fixed test-set case run through the web bridge must store exactly the
figures the engine produces from the command line. Skipped without data.
"""

import pandas as pd
import pytest

from engine import testset
from tests.test_fixed_set import HAVE_DATA

pytestmark = pytest.mark.django_db

CASES = ["base", "shock_0_5", "thresholds_test", "slack_vacancy"]


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
@pytest.mark.parametrize("name", CASES)
def test_ui_matches_engine(name):
    from web.results import bridge
    from web.results.models import ResultRow

    res = testset.run_case(name, allow_unconfirmed=True)
    run = bridge.execute(res.params)
    assert run.run_id == res.run_id
    for table in ("countries", "lines"):
        stored = pd.DataFrame(
            [r.data for r in ResultRow.objects.filter(run=run, table=table)]
        )
        want = res.tables[table].reset_index(drop=True)
        pd.testing.assert_frame_equal(
            stored[want.columns], want, check_dtype=False, rtol=0, atol=0
        )


def test_health(client):
    assert client.get("/health/").json()["status"] == "ok"


def test_login_required(client, settings):
    settings.PUBLIC_READ_ONLY = False
    assert client.get("/").status_code == 302


def test_public_read_only_refuses_runs(client, settings):
    settings.PUBLIC_READ_ONLY = True
    assert client.get("/").status_code == 200
    assert client.get("/new/").status_code == 403


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
def test_front_page_shows_engine_overview(client, settings):
    from engine import results
    from web.results import bridge
    from web.results.templatetags.fmt import bn, hundreds, pct

    settings.PUBLIC_READ_ONLY = True
    res = testset.run_case("base", allow_unconfirmed=True)
    bridge.execute(res.params)
    ov = results.overview(res).iloc[0]
    page = client.get("/").content.decode()
    for shown in (
        pct(ov["headline_jobs_weighted"]),
        f"&euro;{bn(ov['shock_meur'])}bn",
        hundreds(ov["example_extra_persons"]),
        pct(ov["example_pressure"], 1),
    ):
        assert shown in page
