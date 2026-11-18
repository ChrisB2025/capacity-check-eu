"""Create or update the staff login from STAFF_USERNAME and STAFF_PASSWORD.

Runs at container start. The staff account reads reviewer feedback at
/reviewers/feedback/; the shared reviewer login cannot.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the staff login from environment variables."

    def handle(self, *args, **opts):
        name = os.environ.get("STAFF_USERNAME")
        password = os.environ.get("STAFF_PASSWORD")
        if not name or not password:
            self.stdout.write("STAFF_USERNAME or STAFF_PASSWORD not set; no change.")
            return
        if name == os.environ.get("APP_USERNAME"):
            self.stderr.write("STAFF_USERNAME must differ from APP_USERNAME.")
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(username=name)
        user.set_password(password)
        user.is_staff = True
        user.save()
        self.stdout.write(f"Staff user {'created' if created else 'updated'}.")
