from django.conf import settings
from django.contrib.auth.views import redirect_to_login

OPEN_PATHS = ("/health/", "/login/", "/static/")


class LoginRequiredMiddleware:
    """One shared login until the reviewer signs off.

    In public read-only mode results can be read without logging in; starting a
    run is refused to everyone (see ``views.new_run``).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not settings.PUBLIC_READ_ONLY
            and not request.user.is_authenticated
            and not request.path.startswith(OPEN_PATHS)
        ):
            return redirect_to_login(request.get_full_path())
        return self.get_response(request)
