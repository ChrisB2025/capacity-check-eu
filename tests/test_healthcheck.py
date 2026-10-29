"""The Phase 0 health check answers /health/ and nothing else."""

from web.healthcheck import app


def call(path):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status

    body = b"".join(app({"PATH_INFO": path}, start_response))
    return captured["status"], body


def test_health_returns_200():
    status, body = call("/health/")
    assert status.startswith("200")
    assert b'"ok"' in body


def test_other_paths_return_404():
    status, _ = call("/")
    assert status.startswith("404")
