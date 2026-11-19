"""Sign-in for MML EU members, handed over from the MML EU Workspace.

MML Europe's signed-in area shows Active members a "Labs" link. It redirects
here (``/sso/?t=...``) with a token signed with a secret both services hold
(``SSO_SHARED_SECRET`` here, ``LABS_SHARED_SECRET`` there), valid for
``SSO_MAX_AGE`` seconds. The token carries no personal data: an opaque id,
stable per member, and the audience. Each member gets a non-staff account
named after that id, so the shared reviewer login, the staff login and
members stay apart.

The salt and audience must match ``labs/handoff.py`` in the mml-eu repo.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import signing

SALT = "mml-eu.labs.handoff"
AUDIENCE = "capacity-check"
MEMBERS_GROUP = "MML EU members"
SUB_PATTERN = re.compile(r"^m-[0-9a-f]{20}$")


class HandoffError(Exception):
    """The token is missing, forged, expired or not meant for this tool."""


def enabled() -> bool:
    return bool(settings.SSO_SHARED_SECRET)


def verify(token: str) -> str:
    """The member's opaque id from a valid token."""
    if not token:
        raise HandoffError("no token")
    try:
        data = signing.loads(
            token,
            key=settings.SSO_SHARED_SECRET,
            salt=SALT,
            max_age=settings.SSO_MAX_AGE,
        )
    except signing.SignatureExpired as exc:
        raise HandoffError("expired") from exc
    except signing.BadSignature as exc:
        raise HandoffError("bad signature") from exc
    sub = data.get("sub", "") if isinstance(data, dict) else ""
    if data.get("aud") != AUDIENCE or not SUB_PATTERN.match(sub):
        raise HandoffError("wrong audience or id")
    return sub


def member_user(sub: str):
    """The account for this member, created on first visit; never staff."""
    User = get_user_model()
    user, created = User.objects.get_or_create(username=f"mml-{sub}")
    if created:
        user.set_unusable_password()
        user.save()
        group, _ = Group.objects.get_or_create(name=MEMBERS_GROUP)
        user.groups.add(group)
    if user.is_staff or user.is_superuser:
        raise HandoffError("a member account may not be staff")
    return user
