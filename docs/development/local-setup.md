# Local setup

Install uv, Node 24/npm and GNU make. uv manages Python 3.12 through `.python-version`. npm only bootstraps missing pnpm into ignored local tools; frontend dependencies use pnpm 12.18.0 and the root lockfile.

```sh
cp .env.example .env
make setup
make dev
```

Open http://localhost:5173 and choose **Explore demo**. The API listens on loopback 8000; Vite proxies `/api`. Keep browser hostnames consistent with WEB_ORIGIN and cookies. The demo clock is November 5, 2026 in America/Chicago.

Setup synchronizes all eight Python members and the pnpm workspace from their root locks. For manual pnpm commands, use an exact-version executable or the path printed by `uv run python scripts/bootstrap_pnpm.py`. No global installation is required.

Smoke/evaluation expect a running mock API. Tests use isolated data/local servers; stop the dev API before browser tests reserve port 8000. Install Chromium and host libraries with the pinned pnpm using `--filter @mcp-workspace/web exec playwright install --with-deps chromium` where permitted.

Private state stays in `.local/mock` or `.local/live`; never relocate it during a source migration or commit it. Root `artifacts` is scratch space. See [backup/restore](../deployment/operations.md), [devcontainer](../../.devcontainer/devcontainer.json), [runtime containers](../../infra/README.md) and [live setup](../security/oauth-setup.md).
