# MCP Workspace AI — START HERE

**Status:** implementation specification, not implemented software. **Prepared:** 2026-11-05.

## Purpose
This bundle directs an autonomous coding agent such as Codex to **plan, implement, test, document, and package** an end-to-end, portfolio-quality MCP-powered productivity assistant. It is not a toy chat UI or an HTTP API wrapper disguised as an MCP app.

### File map (read in order)
1. `01_CODEX_MASTER_PROMPT.md` — **primary execution instruction** and autonomous engineering contract.
2. `02_PRODUCT_REQUIREMENTS.md` — personas, stories, feature-level definitions of done.
3. `03_TECHNICAL_ARCHITECTURE.md` — system boundaries, tool inventory, API/data contracts, extensibility.
4. `04_SECURITY_AND_OAUTH.md` — threat model, Google OAuth, approval system, data controls.
5. `05_TESTING_AND_EVALUATION.md` — deterministic fixtures, MCP contract, quality, e2e and adversarial tests.
6. `06_MILESTONES_AND_ISSUES.md` — planned milestones and issue backlog for Codex to refine.
7. `07_DEMO_AND_PORTFOLIO.md` — polished demo requirements and career showcase materials.
8. `08_VERIFIED_REFERENCES.md` — official docs and protocol compatibility notes.
9. `AGENTS.md` — permanent repository instructions for Codex.

### How to hand off to Codex
1. Create an empty git repository named `mcp-workspace-ai` (locally is sufficient).
2. Copy **every file in this bundle** to the repository root. Codex will reorganize docs if useful, preserving content.
3. Paste the following message into Codex:

> Read `00_START_HERE.md`, `01_CODEX_MASTER_PROMPT.md`, `AGENTS.md`, and every numbered specification file. You are the lead engineer. First create the detailed implementation plan, issue dependency graph, ADRs, acceptance checklist and CI foundation. Then autonomously implement the entire project milestone by milestone, resolving ordinary engineering decisions yourself. Use `uv`, enforce tests and CI after each issue, create GitHub milestones/issues/project when `gh` is authenticated, and implement mock mode first so no credentials block progress. Do not use my real Gmail or Google account for destructive testing. Explicitly report only actual blockers involving secret credentials, Google OAuth setup, provider accounts, or permissions. Never mark a task complete until its tests and acceptance criteria pass. Begin now.

### Human setup (only when integration is attempted)
- A Google Cloud project and OAuth client ID/secret; configure allowed redirects, test users, scopes, and enable Gmail, Calendar, Drive, Docs, Sheets, Slides APIs.
- An LLM API key, or use local/mock provider instead.
- Optional Google Workspace Developer Preview membership for **Google-hosted MCP** (not required).
- Optional GitHub CLI authentication (`gh auth login`) to create issues and boards. The agent should still create local backlog files when not authorized.

### Recommended delivery strategy
- **MVP:** offline mock data, real MCP server/client traffic, chat + approvals, Gmail/Calendar/Drive read, DOCX/PDF/XLSX/PPTX generation; 100% demoable without private data.
- **Integration release:** real Google OAuth and provider APIs, artifact upload, e2e validation against a controlled test account.
- **Showcase release:** third-party remote MCP client, live MCP inspector, trace UI, tests, security hardening, polished docs/demo.

### Guardrails
The user has asked for Codex to implement, but has **not** granted authorization to send emails, delete files, invite meeting attendees, expose private data publicly, purchase services, or publish/deploy a repository. Those need their own explicit approvals and configured access.
