# Exact-action approval and uncertain outcomes

Status: accepted for the approved core release.

Require confirmation for every Google write, including drafts/uploads/private events. Bind actor, account, tool, canonical arguments, mutable target snapshot and expiration; keep capabilities out of model schemas and consume once in a transaction. Send the approved MIME snapshot atomically with Gmail draft send. Use provider conditional revisions/idempotency where supported. An ambiguous write is outcome_unknown and is never blindly retried; do not claim exactly-once delivery across an unreliable provider network.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
