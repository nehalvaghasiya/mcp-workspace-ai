# Setup and troubleshooting

## Start locally

Use Python 3.12, uv, Node 24, and GNU make. Setup installs the pinned pnpm locally when needed.

```sh
cp .env.example .env
make setup
.venv/bin/python scripts/configure_live.py
make dev
```

Open **http://localhost:5173** and sign in with Google. Enable Gmail read access in Connectors, then review the model provider and allow processing in Settings.

`make dev` starts the API and frontend, or reuses healthy processes for this workspace. Restart the API after Python or configuration changes. Keep the API URL, Vite proxy, and Google callback on the same port.

## Google account

1. In your Google Cloud project, enable the Google APIs for the connectors you intend to use: Gmail, Calendar, Drive, Docs, Sheets, and Slides.
2. Configure a Web application OAuth client. The local browser origin is `http://localhost:5173`; the redirect is `http://localhost:8000/api/auth/google/callback`.
3. For an external app in Testing, add your account under Google Auth Platform → Audience → Test users. The developer-approved-testers error must be resolved in Google Cloud.
4. Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`. Reconnect a connector when adding permissions.

Drive-wide reads require `drive.readonly`. Native Docs, Sheets, and Slides have separate read and write controls. Broader distribution may require Google's OAuth verification. Testing-mode refresh tokens can expire after seven days.

## Model and private storage

Set `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` for your OpenAI-compatible endpoint. A local gateway must be running separately. The model receives only content authorized by the signed-in user's provider-bound consent. Changing the endpoint or model requires reviewing that consent again.

Live mode requires stable `SESSION_SECRET` and `TOKEN_ENCRYPTION_KEY` values. `configure_live.py` prepares missing local configuration without replacing an existing encrypted vault. Keep the encryption key across restarts and backups. Never commit `.env`, browser state, or `.local` data.

Default deadlines are 10 seconds to connect to the model, 60 seconds of read inactivity, 90 seconds total per model call, and 300 seconds per workflow. Adjust `MODEL_CONNECT_TIMEOUT`, `MODEL_READ_TIMEOUT`, `MODEL_REQUEST_TIMEOUT`, and `RUN_TIMEOUT` in `.env`, then restart the API.

Local gateways with slow internal failover may need a larger request budget; this installation uses 150 seconds per request within the 300-second workflow limit. One explicit transient gateway failure may be retried before any response text is published. Google writes are never replayed by this retry.

## Diagnose and recover

```sh
.venv/bin/workspace-ai doctor
.venv/bin/workspace-ai verify-live
```

`doctor` reports effective configuration and model availability without credentials. `verify-live` uses generic model probes and read-only Google checks; it does not establish complete mailbox-summary acceptance. Specify `--user-id` when multiple local accounts exist.

For a failed model response, use **Continue from saved progress** when offered. The continuation reuses completed reads. Actions with write effects are not replayed automatically; inspect activity and the provider before making another request. Saved sources remain available after a failure.

If sign-in fails, check test-user registration, origin, and redirect. If a connector is unavailable, reconnect for its missing grants. For model authentication or quota errors, check the configured gateway's provider connection. A timeout after successful reads concerns the model step, rather than Gmail access.

## Backups

Stop the app before offline maintenance. `workspace-ai backup <directory>` backs up local data; preserve the encryption key separately. `workspace-ai restore <directory>` restores into fresh storage. `workspace-ai rotate-key --help` explains guarded offline key rotation. Keep unredacted recordings and private generated reports out of Git.

See [development](development.md), [architecture and permissions](architecture.md), and [the live demo](../README.md#live-demo).
