from __future__ import annotations

import logging

from .routes import build_routes

log = logging.getLogger("aw_apps.remote-host-terminal")


class RemoteHostTerminalAppPlugin:
    async def activate(self, ctx) -> None:
        ctx.routes.register(build_routes())
        log.info("aw-app-remote-host-terminal activated")

    async def deactivate(self) -> None:
        log.info("aw-app-remote-host-terminal deactivated")
