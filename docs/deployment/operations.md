# Operations

## Local

Prerequisites: uv, Python 3.12 (uv can manage it), Node 24/npm for the local pnpm bootstrap, and GNU make. The project pins pnpm 12.18.0; npm is not a project dependency manager. `make setup` installs both locked dependency sets. `make dev` starts the API on loopback port 8000 and Vite on 5173. Open `http://localhost:5173` with the default WEB_ORIGIN. Keep browser hostnames consistent with cookie/OAuth settings.

State lives under `.local/mock` or `.local/live`; do not put it in Git. Mock secrets are generated with restrictive permissions and persist across restarts. Live mode requires explicit stable secrets. Use HTTPS, correct origins and secure cookies for any deliberately configured nonlocal environment.

`make smoke` expects a running mock API and verifies discovery, cross-app chat and four downloads. `make eval` also expects the mock API; it writes measured synthetic reports. `make test` uses its own isolated TCP servers. `make test-e2e` starts an isolated backend and frontend; stop `make dev` first so port 8000 is available. Install browser dependencies with `pnpm --filter @mcp-workspace/web exec playwright install --with-deps chromium` where permitted.

Health: `/api/health`; readiness/database: `/api/ready`. Connector failures are typed; the MCP Explorer reports independent server health. Startup marks formerly running jobs interrupted and dispatched writes outcome_unknown. No queued write is automatically replayed after restart.

## Backup and recovery

Stop the application before a consistent local backup:

```sh
uv run workspace-ai backup /private/path/new-backup-directory
```

SQLite's backup API captures the database, including WAL state; artifacts are copied separately. Keep the encryption key and its TOKEN_KEY_VERSION privately with the backup procedure, not inside a published archive. With the app stopped and the original key/mode configured, restore into a fresh DATA_DIR:

```sh
DATA_DIR=/private/path/fresh-storage uv run workspace-ai restore /private/path/new-backup-directory
```

Restore refuses existing database/artifact storage, symlink trees and a wrong credential key. It preserves encrypted credentials and artifact bytes; it does not merge databases. A backup contains private app data and must remain private. Do not copy only a live `.db` while ignoring WAL files. Never reset live storage using demo commands.

For credential-key rotation, stop the app, take a backup, and supply the replacement Fernet key privately as NEW_TOKEN_ENCRYPTION_KEY in the operator environment. Keep the current TOKEN_ENCRYPTION_KEY configured while running:

```sh
uv run workspace-ai rotate-key --key-version v2
```

The command decrypts and re-encrypts all live credential rows in one transaction, records the nonsecret key version, and leaves mock rows unchanged. It prints no key/token values. Before restarting, replace TOKEN_ENCRYPTION_KEY with the new key and set TOKEN_KEY_VERSION to v2 in private configuration; remove NEW_TOKEN_ENCRYPTION_KEY from the process environment. Keep the old key securely only for backups that still require it. Invalid rows abort the whole rotation.

The CLI seed/reset operations are restricted to mock mode and affect the synthetic CLI fixture account. They do not reset a currently signed-in browser's data or access Google.

## Containers and CI

`docker compose up --build --wait` runs the mock service with a persistent volume and loopback-only published port. The image builds the frontend, installs backend dependencies through uv, runs as a nonroot user and includes licensed document fonts. `docker compose exec -T workspace workspace-ai smoke` checks the container. Container execution status is recorded in the verification handoff; a Dockerfile alone is not deployment evidence.

The configured GitHub Actions workflows run quality, real-protocol/backend tests, browser tests and container smoke without cloud credentials. Remote CI status remains unverified until the repository workflow actually runs. Public publishing/deployment is a separate explicit action.

The pre-reorganization Docker/Compose checks both passed; see [container proof](../../demo/evidence/baseline/container-proof.json) and [Compose proof](../../demo/evidence/baseline/compose-proof.json). This WSL host had stale Docker Desktop plugin symlinks: verification used a temporary Docker config with `cliPluginsExtraDirs` selecting the installed `/usr/libexec/docker/cli-plugins`. No global Docker configuration or project Compose behavior was changed. The temporary test project and volume were removed afterward.

To reproduce the isolated no-network smoke independently of Compose:

```sh
docker buildx build --load --target api -f infra/docker/base.Dockerfile -t mcp-workspace-ai:local .
docker run -d --name workspace-offline-check --network none --memory 8g --cpus 2 --read-only --cap-drop ALL --security-opt no-new-privileges:true --tmpfs /app/.local:uid=10001,gid=10001,mode=0700,size=256m --tmpfs /tmp:rw,nosuid,nodev,size=64m mcp-workspace-ai:local
docker exec workspace-offline-check workspace-ai smoke
docker exec workspace-offline-check python -c "from pathlib import Path; print(Path('/sys/fs/cgroup/memory.peak').read_text())"
docker stop workspace-offline-check
docker rm workspace-offline-check
```

Wait for the container readiness check before smoke. The name above must be unused. This removes only that temporary check container; use Compose's persistent volume for normal local work. If port 8000 is still held immediately after browser tests, allow it to release before starting Compose.

## Known operating limits

One backend process is the supported local topology. SQLite and bounded in-process execution are used instead of a distributed queue. Adding multiple API workers needs explicit shared scheduling/locking work. Internal MCP assertions must not be exposed as a public OAuth service. Full Google verification, restricted-scope assessments, real-model quality and native Office rendering are separate checks.

RETENTION_DAYS defaults to 30; startup and hourly cleanup remove expired inactive conversations, their dependent records and files. Active conversations are excluded until work finishes. Users can delete individual conversations or all local account data immediately. Default quotas are 100 artifacts per user, 10 MiB per output and 100 MiB total per user; two renderer workers are allowed. Settings validation documents the configurable bounds. Disk storage and backup retention remain operator responsibilities.

The default container build is `infra/docker/base.Dockerfile` target `api`; [component image instructions](../../infra/README.md) describe the diagnostic wrappers. Fresh post-migration verification is recorded separately from baseline evidence.
