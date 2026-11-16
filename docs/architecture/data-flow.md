# Data flow and provenance

Server-side OIDC establishes an app identity. Incremental connector consent is bound to that identity and active session. Credentials remain encrypted; the browser receives an opaque cookie and app CSRF token.

A message becomes an owned conversation/run. The model receives authorized evidence and contracts, with separate live-content consent. Execution capabilities remain in trusted server-side context.

Reads return ToolResult and SourceRef records containing provider, ID, title, retrieval time and bounded pointers/snippets. Retrieved text is untrusted evidence. References propagate into answers, cards, trace metadata and artifact provenance.

A document specification is rendered to temporary owner-derived storage, reopened and checked structurally and semantically before atomic publication. Metadata records format, size, checksum, sources and an authenticated download URL.

Approvals bind normalized arguments, target/content revision and operation identity. Durable write outcomes survive UI disconnection; uncertain effects are not guessed successful or automatically resent.

Deletion removes local owned state and fences in-flight work. It cannot recall provider-accepted requests or delete Google resources. See [privacy](../security/data-privacy.md) and [operations](../deployment/operations.md).
