"""routes.py's WebSocket relay (2026-08-29): host_to_browser caught Exception
and returned with zero trace -- a real bug in the relay looked identical to a
normal client disconnect. Now logs a warning (not notify_sysadmins: this
fires on ordinary network noise like a host reboot or wifi drop, which would
page on every normal disconnect if escalated that far).

Run: python3 -m pytest tests/test_terminal_relay_log.py
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from remote_host_terminal_app.backend import BackendConfig
from remote_host_terminal_app.routes import build_routes


class _RaisingUpstream:
    """Stands in for the websockets.connect() result: iterating it raises
    mid-stream, the way a dropped host-side connection does."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise RuntimeError("connection reset by peer")

    async def send(self, _data):
        pass

    async def close(self):
        pass


def test_host_to_browser_logs_instead_of_swallowing(caplog):
    caplog.set_level(logging.WARNING, logger="aw_apps.remote_host_terminal")
    config = BackendConfig("https://backend.example", "demo", "secret")

    with patch("remote_host_terminal_app.routes.websockets.connect", AsyncMock(return_value=_RaisingUpstream())):
        with TestClient(build_routes(lambda: config)).websocket_connect("/ws/hosts/h1") as ws:
            # host_to_browser's async-for over the upstream raises immediately;
            # the route's finally-block then closes this end too.
            try:
                ws.receive_text()
            except Exception:
                pass

    assert any(
        "host_to_browser stream ended unexpectedly" in r.message
        for r in caplog.records
    )
