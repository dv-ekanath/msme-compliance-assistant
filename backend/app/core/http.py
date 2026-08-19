from __future__ import annotations

from collections.abc import Generator

import httpx


def get_http_client() -> Generator[httpx.Client, None, None]:
    """FastAPI dependency yielding a request-scoped httpx.Client, mirroring
    get_db's open/close shape. Tests override this via
    `dependency_overrides` with an `httpx.MockTransport`-backed client --
    the standard way to test real httpx code, no bespoke abstraction.
    """
    client = httpx.Client(timeout=10.0, follow_redirects=True)
    try:
        yield client
    finally:
        client.close()
