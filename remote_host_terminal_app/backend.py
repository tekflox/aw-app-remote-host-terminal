"""Shared aw-backend channel configuration.

This deliberately mirrors aw-app-remote-host-cli's transport contract without
importing that app: both independently use AW_BACKEND_URL, AW_WORKSPACE and
AW_WORKSPACE_HOST_TOKEN and the same account-scoped remote-host endpoints.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote


class NotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class BackendConfig:
    backend_url: str
    workspace: str
    token: str

    @classmethod
    def from_env(cls) -> "BackendConfig":
        config = cls(
            backend_url=os.environ.get("AW_BACKEND_URL", "http://127.0.0.1:9025").rstrip("/"),
            workspace=os.environ.get("AW_WORKSPACE", "").strip(),
            token=os.environ.get("AW_WORKSPACE_HOST_TOKEN", "").strip(),
        )
        if not config.workspace or not config.token:
            raise NotConfigured(
                "AW_WORKSPACE and AW_WORKSPACE_HOST_TOKEN must be configured before remote hosts can be accessed."
            )
        return config

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def hosts_url(self) -> str:
        return f"{self.backend_url}/api/workspaces/{quote(self.workspace, safe='')}/remote-hosts"

    def shell_url(self, host_id: str) -> str:
        base = self.backend_url
        if base.startswith("https://"):
            base = "wss://" + base[8:]
        elif base.startswith("http://"):
            base = "ws://" + base[7:]
        return (
            f"{base}/api/workspaces/{quote(self.workspace, safe='')}/remote-hosts/"
            f"{quote(host_id, safe='')}/shell?target=host"
        )
