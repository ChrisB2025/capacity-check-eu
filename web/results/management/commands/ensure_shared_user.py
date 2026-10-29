"""Create or update the single shared login from APP_USERNAME and APP_PASSWORD.

Runs at container start. The password lives only in the Railway variable.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the shared login from environment variables."

    def handle(self, *args, **opts):
        name = os.environ.get("APP_USERNAME")
        password = os.environ.get("APP_PASSWORD")
        if not name or not password:
            self.stdout.write("APP_USERNAME or APP_PASSWORD not set; no change.")
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(username=name)
        user.set_password(password)
        user.save()
        self.stdout.write(f"Shared user {'created' if created else 'updated'}.")
