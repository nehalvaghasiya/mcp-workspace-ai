# MCP Workspace AI

A workspace assistant for your Gmail, Calendar, Drive, Docs, Sheets, and Slides. Ask questions, inspect sources and tool activity, and create native Google files or downloadable reports. Google changes require approval for the exact action.

## Live demo





https://github.com/user-attachments/assets/4b305471-56e2-4116-854e-ccad50dd0cc1



[Open or download the full demo (3 minutes)](demo/workspace-live.mp4?raw=true#t=0.1) - use the player controls to pause, seek, change volume, or enter fullscreen. The demo summarizes emails, prioritizes next steps, and downloads a PDF with sources.

*Personal and email details are hidden to protect privacy.*

## Start

Requires Python 3.12, uv, Node 24, and GNU make. Setup installs the pinned pnpm locally.

```sh
cp .env.example .env
make setup
.venv/bin/python scripts/configure_live.py
make dev
```

Configure Google OAuth and your model in `.env`, then open **http://localhost:5173**. Sign in with Google, enable connectors, and review model processing in Settings. See [setup and troubleshooting](docs/setup.md) for the complete account configuration.

Try:

> Summarize my five most recent inbox emails and highlight decisions and next steps.

> Check my meetings this week and identify scheduling conflicts.

> Turn these findings into a PDF brief with sources.

## Useful commands

| Command | Purpose |
|---|---|
| `make dev` | Run the live workspace |
| `.venv/bin/workspace-ai doctor` | Diagnose effective configuration and model availability |
| `.venv/bin/workspace-ai verify-live` | Check the model and read-only Google access |
| `make test-e2e` | Run isolated browser workflows |
| `make ci` | Run the complete verification gate |

The app saves sources and completed reads when a model request fails. **Continue from saved progress** resumes eligible read-only workflows. Activity shows the actual failure and completed actions.

## Guides

- [Setup](docs/setup.md): Google OAuth, model configuration, troubleshooting, and backups.
- [Development](docs/development.md): tests, builds, evaluations, and contribution rules.
- [Architecture](docs/architecture.md): MCP boundaries, approvals, ownership, and data handling.

Python packages share one uv lockfile; frontend packages share one pnpm lockfile. Mock fixtures remain isolated from live operation. Generated reports, browser state, and private artifacts stay under ignored `.local/` directories.

MIT licensed. Bundled font notices accompany their assets.
