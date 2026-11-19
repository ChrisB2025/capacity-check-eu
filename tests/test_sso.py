"""Sign-in handed over from the MML EU Workspace (web/results/sso.py).

Tokens are made exactly as mml-eu's labs/handoff.py makes them.
"""

import time
from unittest import mock

import pytest
from django.core import signing

pytestmark = pytest.mark.django_db

SECRET = "test-labs-secret"
SUB = "m-0123456789abcdef0123"


def token(sub=SUB, aud="capacity-check", key=SECRET):
    return signing.dumps({"sub": sub, "aud": aud}, key=key, salt="mml-eu.labs.handoff")


@pytest.fixture
def sso_on(settings):
    settings.SSO_SHARED_SECRET = SECRET
    settings.PUBLIC_READ_ONLY = False


def test_valid_token_signs_in_a_non_staff_member(client, sso_on):
    from django.contrib.auth import get_user_model

    r = client.get(f"/sso/?t={token()}")
    assert r.status_code == 302 and r["Location"] == "/"
    user = get_user_model().objects.get(username=f"mml-{SUB}")
    assert not user.is_staff and not user.has_usable_password()
    assert user.groups.filter(name="MML EU members").exists()
    assert client.get("/glossary/").status_code == 200  # signed in
    assert client.get("/reviewers/feedback/").status_code == 403  # not staff


def test_same_member_same_account(client, sso_on):
    from django.contrib.auth import get_user_model

    client.get(f"/sso/?t={token()}")
    client.get(f"/sso/?t={token()}")
    assert get_user_model().objects.filter(username=f"mml-{SUB}").count() == 1


@pytest.mark.parametrize(
    "bad",
    [
        token(key="another-secret"),
        token(aud="something-else"),
        token(sub="chris@example.eu"),
        "not-a-token",
        "",
    ],
)
def test_bad_tokens_are_refused(client, sso_on, bad):
    r = client.get(f"/sso/?t={bad}")
    assert r.status_code == 403
    assert "Labs in the MML EU Workspace" in r.content.decode()
    assert client.get("/glossary/").status_code == 302  # still signed out


def test_expired_token_is_refused(client, sso_on):
    t = token()
    with mock.patch("time.time", return_value=time.time() + 120):
        assert client.get(f"/sso/?t={t}").status_code == 403


def test_closed_without_a_secret(client, settings):
    settings.SSO_SHARED_SECRET = ""
    settings.PUBLIC_READ_ONLY = False
    assert client.get(f"/sso/?t={token()}").status_code == 404


def test_login_page_points_members_to_labs(client, settings):
    settings.PUBLIC_READ_ONLY = False
    assert "Labs in the MML EU Workspace" in client.get("/login/").content.decode()
