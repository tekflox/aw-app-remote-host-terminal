# Remote Host Terminal

- **repo**: aw-app-remote-host-terminal
- **layer**: app
- **technologies**: Python, FastAPI, React, xterm.js

Tier-1 workspace app that lists every non-revoked remote host belonging to the
current account and opens multiple interactive host terminals in one window.

## Communication contract

This app and `aw-app-remote-host-cli` are independent consumers of the same
aw-backend contract. Neither imports, installs, or deploys the other:

- host discovery: `GET /api/workspaces/{slug}/remote-hosts`
- terminal: `WS /api/workspaces/{slug}/remote-hosts/{host_id}/shell?target=host`
- actor credential: `AW_WORKSPACE_HOST_TOKEN`
- terminal frames: `input`, `output`, `resize`, and `status`

The browser never receives the actor credential. Its authenticated app-local
WebSocket terminates in the Tier-1 plugin, which opens the upstream connection
and relays the existing JSON protocol. Each browser tab owns one upstream PTY;
unmounting the tab or app window closes it.

Windows behavior belongs to `aw-remote-host`, not this app: the same `pty_open`
frame is implemented with ConPTY and launches `pwsh` or Windows PowerShell.
