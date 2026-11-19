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


# Review of 18 November 2026: glossary, risk label, reviewer page.


def test_glossary_page_lists_every_term(client, settings):
    from engine import text

    settings.PUBLIC_READ_ONLY = True
    page = client.get("/glossary/").content.decode()
    for t in text.glossary():
        assert f'id="{t["slug"]}"' in page
    assert text.RISK_LABEL in page


def _answers(**kw):
    return {"name": "A Reviewer", "weakest": "The composition.", **kw}


def test_feedback_is_saved(client, settings):
    from web.results.models import Feedback

    settings.PUBLIC_READ_ONLY = True
    assert client.get("/reviewers/").status_code == 200
    r = client.post("/reviewers/", _answers())
    assert r.status_code == 302 and "sent=1" in r["Location"]
    fb = Feedback.objects.get()
    assert fb.weakest == "The composition." and fb.name == "A Reviewer"


def test_feedback_honeypot_and_empty_answers(client, settings):
    from web.results.models import Feedback

    settings.PUBLIC_READ_ONLY = True
    assert client.post("/reviewers/", _answers(website="spam")).status_code == 302
    assert client.post("/reviewers/", {"name": "No answers"}).status_code == 400
    assert Feedback.objects.count() == 0


def test_feedback_list_is_staff_only(client, settings):
    from django.contrib.auth import get_user_model

    from web.results.models import Feedback

    settings.PUBLIC_READ_ONLY = False
    Feedback.objects.create(trust="Show the sources.")
    User = get_user_model()
    shared = User.objects.create_user("shared", password="x")
    client.force_login(shared)
    assert client.get("/reviewers/feedback/").status_code == 403
    staff = User.objects.create_user("staff", password="x", is_staff=True)
    client.force_login(staff)
    page = client.get("/reviewers/feedback/")
    assert page.status_code == 200 and "Show the sources." in page.content.decode()
    assert (
        "Show the sources."
        in client.get("/reviewers/feedback/?format=csv").content.decode()
    )


def test_ensure_staff_user(monkeypatch):
    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    monkeypatch.setenv("STAFF_USERNAME", "chris")
    monkeypatch.setenv("STAFF_PASSWORD", "secret")
    monkeypatch.setenv("APP_USERNAME", "reviewers")
    call_command("ensure_staff_user")
    u = get_user_model().objects.get(username="chris")
    assert u.is_staff and u.check_password("secret")


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
def test_results_pages_explain_themselves(client, settings):
    from engine import text

    settings.PUBLIC_READ_ONLY = True
    res = testset.run_case("base", allow_unconfirmed=True)
    run = bridge_execute(res)
    rid = run.run_id
    pages = {
        "overview": "/",
        "run": f"/run/{rid}/",
        "country": f"/run/{rid}/country/DE/",
        "sweden": f"/run/{rid}/sweden/",
        "thresholds": f"/run/{rid}/thresholds/",
    }
    html = {}
    for name, url in pages.items():
        r = client.get(url)
        assert r.status_code == 200, url
        html[name] = r.content.decode()
        assert text.RISK_LABEL in html[name], f"risk label missing on {name}"
        assert "{pressure_low}" not in html[name]
    for shown in ("In brief", "How the shock is allocated", "41, 42, 43",
                  "Named limit: one shock, 27 different countries",
                  "You cannot compare", "Jobs are not hires",
                  "Insulation workers", "Estimated risk category"):  # fmt: skip
        assert shown in html["run"], shown
    assert "What this could mean" in html["country"]
    assert "Options to consider, not recommendations" in html["country"]
    assert "Why these cut-offs" in html["thresholds"]
    csv_lines = client.get(f"/run/{rid}/csv/lines.csv").content.decode().splitlines()
    assert csv_lines[1] == f"# {text.RISK_LABEL}"


def bridge_execute(res):
    from web.results import bridge

    return bridge.execute(res.params)


def test_ordinal_filter():
    from web.results.templatetags.fmt import ordinal

    assert ordinal(0.863) == "86th"
    assert ordinal(0.21) == "21st"
    assert ordinal(0.12) == "12th"
    assert ordinal(None) == "n/a"


@pytest.mark.skipif(not HAVE_DATA, reason="processed data not present")
def test_explainer_for_any_run_and_ciaran_questions(client, settings):
    settings.PUBLIC_READ_ONLY = True
    res = testset.run_case("shock_0_5", allow_unconfirmed=True)
    run = bridge_execute(res)
    page = client.get(f"/run/{run.run_id}/explain/").content.decode()
    assert "0.5% of" in page and "The step-by-step explainer for this run" in page
    run_page = client.get(f"/run/{run.run_id}/").content.decode()
    expected = ("of which at home", "percentile)", "jobs</span>",
                "Pressure: Wholesale trade", "How to read a small share")  # fmt: skip
    for shown in expected:
        assert shown in run_page, shown
    assert client.get("/run/nope/explain/").status_code == 404


def test_data_page_shows_ladder_and_machine_verdict(client, settings):
    from engine import text

    settings.PUBLIC_READ_ONLY = True
    page = client.get("/data/").content.decode()
    d = text.data_ladder()
    from django.utils.html import escape

    assert escape(d["verdict"]["label"]) in page and "machine judgement" in page
    for step in d["ladder"]:
        assert escape(step["step"]) in page
    assert "Chris Bland" not in page  # the verdict is in no one's name
