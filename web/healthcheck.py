"""Phase 0 placeholder WSGI app: a health check and nothing else.

It proves the Railway build and deploy path before the Django project exists.
Phase 4 replaces it with the Django project in this folder, and the Dockerfile
gains the collectstatic and migrate steps then.
"""

import json


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path.rstrip("/") == "/health":
        body = json.dumps({"status": "ok", "phase": 0}).encode()
        status = "200 OK"
    else:
        body = b"Capacity Check Europe: not yet published."
        status = "404 Not Found"
    content_type = "application/json" if status.startswith("200") else "text/plain"
    start_response(
        status,
        [("Content-Type", content_type), ("Content-Length", str(len(body)))],
    )
    return [body]
