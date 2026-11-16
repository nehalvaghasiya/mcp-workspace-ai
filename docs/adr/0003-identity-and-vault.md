# OIDC identity and an encrypted server-side vault

Status: accepted for the approved core release.

Google OIDC establishes app identity; connector scopes are incrementally consented. One Google subject per app user keeps account binding explicit. App sessions are opaque, hashed and server-side. Encrypt OAuth credentials with a stable Fernet key and track key versions. Offline rotation is transactional; operators stop the service and update private key configuration afterward. Session state, scopes, consent and ownership remain outside model control. Authlib is pinned below 2 because its tested JOSE API is deprecated before that boundary; migration to joserfc should accompany a future major upgrade.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
