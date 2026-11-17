# Threat model

Assets are Google credentials, private source content, app sessions, user-owned rows/files, approval capabilities, and the integrity of external actions. Trusted components are the configured single backend process, local database/filesystem, operator configuration and installed renderer/SDK dependencies. Email/document text, model responses, browser inputs, discovered descriptions and provider responses are untrusted.

| Boundary / threat | Implemented control | Baseline verification |
|---|---|---|
| Browser → API: session theft, CSRF, oversized input | Opaque hashed sessions, HttpOnly cookie, exact Origin, CSRF, counted body limit, no submitted-value reflection | API/security tests |
| Google → callback: forged identity, state replay, account substitution | Signed OIDC claims, nonce, PKCE, consumed browser-bound state, same-subject connector binding | OAuth/identity tests with signed fixtures |
| Vault → provider: credential disclosure or stale refresh | Fernet, no browser/model tokens, serialized refresh, disconnect/deletion fence, offline atomic rotation | Vault/security tests |
| Model → MCP: unauthorized or changed action | Trusted registry, bounded typed calls, scoped audience assertions, policy recheck, one-use exact-action approval | Protocol, approval race/replay tests |
| Source → model: prompt injection/exfiltration | Data/instruction separation, no capabilities in context, no arbitrary URL/network tools, server-enforced write approvals | Injection/canary tests; W11 |
| User A → user B: guessed IDs/cache paths | Owner predicates on all routes/policy, owner-derived directories, isolated fixture state, tombstone on deletion | API/protocol/deletion-race tests |
| Parser → filesystem/process: archive bombs, traversal, active documents | Bounded native export/text extraction, ZIP/XML checks, no macros/active links, generated paths, bounded render workers | Extraction/artifact tests |
| Workbook → recipient: formula injection | Literal untrusted strings; explicit allowlisted arithmetic formulas | Renderer semantic readback tests |
| Retry/restart → provider: duplicate effects | Durable operation claim, no write retry after dispatch, outcome_unknown, persisted interrupted state | Ambiguous-outcome/replay/restart tests |
| Operator → deployment: overexposure or false readiness | Loopback private MCP, single-worker topology, scoped deployment claims, separate live validation | Docker no-network smoke; handoff limitations |

Account/conversation deletion cancels and waits for local generation cleanup. A request already accepted by Google may have an external effect; local deletion cannot recall it. Source content is retained in private conversations when needed for answers, but raw bodies and credentials are excluded from tool traces/logs.

Residual risks: renderer/provider dependencies, a compromised backend/operator, real-model factual errors, unknown provider outcomes, and untested native Office layout. Public multi-tenant operation needs Google app verification, appropriate assessment and independent review. Optional third-party MCP onboarding is excluded.

See [security controls and limits](data-privacy.md), [OAuth setup](oauth-setup.md), [operations](../deployment/operations.md), and [actual verification](../verification/historical/core-handoff.md).
