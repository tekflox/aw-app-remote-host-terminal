"""App-local HTTP and WebSocket proxy for the shared remote-host channel."""
from __future__ import annotations

import asyncio
import json
import logging

import httpx
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .backend import BackendConfig, NotConfigured

log = logging.getLogger("aw_apps.remote_host_terminal")


def build_routes(config_factory=BackendConfig.from_env) -> FastAPI:
    app = FastAPI(title="Remote Host Terminal")

    @app.get("/hosts")
    async def list_hosts():
        try:
            config = config_factory()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(config.hosts_url, headers=config.headers)
            try:
                data = response.json()
            except ValueError:
                data = {}
            if response.status_code >= 400:
                detail = data.get("error") or data.get("detail") or f"HTTP {response.status_code}"
                return JSONResponse({"error": detail}, status_code=response.status_code)
            return data
        except NotConfigured as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        except httpx.HTTPError as exc:
            return JSONResponse({"error": str(exc)}, status_code=502)

    @app.websocket("/ws/hosts/{host_id}")
    async def terminal(ws: WebSocket, host_id: str):
        await ws.accept()
        try:
            config = config_factory()
        except NotConfigured as exc:
            await ws.send_json({"op": "status", "state": "offline", "message": str(exc)})
            await ws.close(code=4503)
            return

        try:
            upstream = await websockets.connect(
                config.shell_url(host_id),
                additional_headers=config.headers,
                open_timeout=15,
                close_timeout=5,
                max_size=None,
            )
        except Exception as exc:  # websockets exposes several handshake/transport exception types
            await ws.send_json({"op": "status", "state": "offline", "message": str(exc)})
            await ws.close(code=4502)
            return

        async def browser_to_host():
            try:
                while True:
                    raw = await ws.receive_text()
                    message = json.loads(raw)
                    if message.get("op") in {"input", "resize"}:
                        await upstream.send(json.dumps(message))
            except (WebSocketDisconnect, ValueError, RuntimeError):
                return

        async def host_to_browser():
            try:
                async for raw in upstream:
                    await ws.send_text(raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace"))
            except Exception:
                # Broad on purpose: the host side of a live terminal stream can fail
                # in ways websockets does not expose as a narrow exception type. Silent
                # before this fix -- log it so a real bug shows up somewhere instead of
                # looking identical to a normal disconnect.
                log.warning("remote-host-terminal: host_to_browser stream ended unexpectedly", exc_info=True)
                return

        tasks = [asyncio.create_task(browser_to_host()), asyncio.create_task(host_to_browser())]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            await upstream.close()
            try:
                await ws.close()
            except RuntimeError:
                pass

    return app
