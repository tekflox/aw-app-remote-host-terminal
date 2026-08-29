# aw-app-remote-host-terminal

Open multiple interactive browser terminals on remote hosts linked to the
current aw-workspace account. Linux and macOS hosts use a PTY; Windows hosts
use the aw-remote-host ConPTY implementation (`pwsh`, then Windows PowerShell).

The app is independent from `aw-app-remote-host-cli`. Both use the same
account-scoped aw-backend contract and credential:

- `GET /api/workspaces/{workspace}/remote-hosts`
- `WS /api/workspaces/{workspace}/remote-hosts/{host_id}/shell?target=host`
- `Authorization: Bearer $AW_WORKSPACE_HOST_TOKEN`

The Tier-1 backend keeps that credential out of browser JavaScript and proxies
the shell's JSON input/output/resize frames through its authenticated app route.
Each tab owns one upstream PTY and closing a tab or the app window closes it.

## Development

```bash
python -m pytest
python tests/validate_manifest.py aw-app.json
cd ui && npm install && npm run build
```
