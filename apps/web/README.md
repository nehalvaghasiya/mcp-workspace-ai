# Workspace frontend

React 19, strict TypeScript, Vite, TanStack Query and Tailwind. Node 24 and pinned pnpm 12.18.0 are used through the root workspace. Run `make setup` and `make dev` from the repository root. Dependencies use only the root pnpm-lock.yaml; generated contracts live in packages/shared-types.

The app lives in app/routes/providers; components have one component per file. Feature hooks own conversation, settings and tool-event behavior. Network services retain HttpOnly cookies, CSRF and idempotent request IDs; credentials are not stored in the browser. Existing hash routes and API URLs are unchanged.

`make test-e2e` starts a disposable mock backend and Vite, and refuses an occupied backend port. Seven browser cases use explicit UI fixtures; three exercise the actual mock backend and MCP calls, four artifact downloads/history, rejection and separate draft/send approvals. New actual captures go to demo/screenshots/reorganization. Controlled fixture captures/QA evidence remain under apps/web/qa and do not establish MCP execution.

Install Chromium dependencies with `pnpm --filter @mcp-workspace/web exec playwright install --with-deps chromium` on a suitable development host. This WSL host already has Chromium installed and supplies missing runtime libraries through `LD_LIBRARY_PATH=/tmp/workspace-browser-libs/extracted/usr/lib/x86_64-linux-gnu` for browser checks. CI installs system dependencies explicitly.

Use `make lint`, `make format-check`, `make typecheck`, `make schema-check`, `make test` and `make build`. Package-specific commands can run through the pinned local executable under .local/tools/pnpm, with that bin directory on PATH. No global pnpm installation is required.
