# One resumable agent loop

Status: accepted for the approved core release.

Use a bounded single-agent loop with persisted run progress and SSE event IDs. FakeLLM follows curated synthetic routines and never contacts a model provider; real tool-calling uses a configured OpenAI-compatible endpoint only in live mode with provider-bound per-user sharing consent. Resume exact approved steps without regenerating their arguments. Cancel future steps, fence background render cleanup and retain actual dispatched-write outcome. This avoids a second state machine in an orchestration framework.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
