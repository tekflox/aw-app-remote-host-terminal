from __future__ import annotations

import os
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from remote_host_terminal_app.backend import BackendConfig, NotConfigured
from remote_host_terminal_app.routes import build_routes


def test_shell_url_uses_shared_plural_channel_and_host_target():
    config = BackendConfig("https://backend.example", "my workspace", "secret")
    assert config.shell_url("host/1") == (
        "wss://backend.example/api/workspaces/my%20workspace/remote-hosts/host%2F1/shell?target=host"
    )


def test_missing_workspace_credentials_fail_loudly():
    with patch.dict(os.environ, {"AW_WORKSPACE": "", "AW_WORKSPACE_HOST_TOKEN": ""}, clear=False):
        try:
            BackendConfig.from_env()
        except NotConfigured as exc:
            assert "AW_WORKSPACE" in str(exc)
        else:
            raise AssertionError("missing credentials were accepted")


def test_hosts_route_proxies_account_scoped_listing():
    config = BackendConfig("https://backend.example", "demo", "secret")
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"count": 1, "hosts": [{"id": "h1", "connected": True}]}
    client = AsyncMock()
    client.get.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = client
    with patch("remote_host_terminal_app.routes.httpx.AsyncClient", return_value=context):
        result = TestClient(build_routes(lambda: config)).get("/hosts")
    assert result.status_code == 200
    assert result.json()["hosts"][0]["id"] == "h1"
    client.get.assert_awaited_once_with(config.hosts_url, headers=config.headers)
