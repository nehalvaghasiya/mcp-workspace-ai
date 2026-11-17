# Security and privacy controls

This is a security-aware prototype, not a certification or claim of enterprise readiness. Synthetic data is used in default development and CI.

## Boundaries

- App sessions use random opaque identifiers stored as hashes, HttpOnly SameSite cookies, expiry, CSRF tokens, and exact configured Origin checks. Live cookies require HTTPS outside local development.
- Google OIDC validates signature, issuer, audience, expiry and nonce. OAuth state/PKCE is short-lived, browser-bound and consumed once. Connector consent must match the signed-in Google subject and an active initiating session.
- Google tokens are encrypted using Fernet with a stable operator-supplied key in live mode. They are never sent to the browser, model, MCP schema or trace. Refresh is serialized; disconnect/deletion fences late refresh responses.
- Connector disable is local. Google revocation affects the combined project grant, so every affected connector and pending approval is invalidated. No claim is made that a previously issued remote request can be recalled.
- Live content may enter the configured model only after that user consents to the current provider/model configuration. This is separate from Google scopes. Mock mode requires FakeLLM.
- Internal MCP assertions bind actor, server audience, allowed tools and expiry. HTTP also checks Origin and host protections. Stdio requires an assertion supplied through environment, never a shell string or token command argument.
- Every Google write is approved at the downstream tool boundary. Approvals bind normalized arguments, account, target revision/content, expiry and a one-use capability. The model never receives execution capabilities.
- Reads have bounded retries. Dispatched non-idempotent writes are not blindly retried; unknown outcomes remain unknown until reconciled with the provider.

## Data and resource limits

Browser/MCP request bodies are counted up to 1 MB even when chunked. Submitted values are excluded from validation error responses. Chat input is bounded to 8,000 characters; list calls cap at 50 records and file text at 20,000 characters. Default runs allow 24 tools, a 180-second active execution timeout, and 30-second tool deadlines. Approval expiry is five minutes.

Artifact IR is capped at 500 KB, tables/workbooks at 1,000 rows, presentations at 50 slides, PDF at 200 pages and output files at 10 MB by default. Office ZIP members, decompressed bytes, expansion ratios and active relationships/macros are checked. External images, executable templates and arbitrary filesystem paths are unsupported. Untrusted spreadsheet text remains literal; formulas require an explicit safe arithmetic type and are not calculated by openpyxl.

Files use opaque generated names in owner-derived directories. Rendering publishes only after structural and semantic readback. Downloads are authenticated attachments, including HTML. Cancellation waits for background render cleanup before account/conversation deletion finishes. Source bodies are not written to tool traces; answers and conversation state remain private user data.

## Baseline security verification

OAuth state/nonce/signature failures, scope narrowing, revoked access, logged-out callbacks, cross-user access, approval argument edits and races, changed drafts, duplicate decisions, ambiguous provider outcomes, prompt-injection fixtures, secret canaries, path traversal, macro/ZIP/XML/PDF attacks, request-size bypasses, disabled connector access and deletion races.

The preserved core baseline exercised these threats. Post-migration gate results are recorded separately.

`make security` runs dependency advisory audits, Bandit, security regressions and source secret checks. Advisory audits require network access; the mock application tests do not call Google or model services. A heuristic secret scan is not a complete credential audit. See the [threat model](threat-model.md). Before any public live distribution, complete the applicable Google verification, privacy disclosures, security assessment and independent review.
