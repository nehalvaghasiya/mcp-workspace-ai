# Security policy

Default development and CI use synthetic data and FakeLLM. Google credentials stay encrypted server-side; every Google write requires exact-action approval at the MCP boundary. The private MCP endpoints use scoped host assertions and are not a public OAuth service for arbitrary clients.

Never include tokens, credentials, raw mailbox/document content, session cookies or private logs in a public issue. Use the repository's private vulnerability reporting when enabled. Otherwise establish a private contact with the maintainer through their verified repository profile before sharing exploit details. No security contact address is invented here.

Report the affected version or source revision, reproduction using synthetic data, expected/actual behavior and impact. Coordinate any real-account investigation with controlled resources and explicit authorization. Do not send messages, change remote resources or test another user's data without permission.

See [threat model](docs/security/threat-model.md), [approval policies](docs/security/approval-policies.md) and [data privacy](docs/security/data-privacy.md). Dependency advisory checks are point-in-time results, and a local test pass is not an independent security assessment.
