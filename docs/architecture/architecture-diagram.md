# Architecture diagram

```mermaid
flowchart LR
    UI[React web] -->|REST and SSE| API[FastAPI application]
    API --> Agent[Bounded agent and persisted runs]
    Agent --> Client[Official MCP client]
    Client -->|Actual loopback HTTP| Servers[Gmail / Calendar / Drive / Artifact / Demo]
    Servers --> Guard[Signed actor / scope / owner checks]
    Guard --> Context[Shared execution context]
    Context --> Approval[Exact-action operation transaction]
    Context --> Providers[Mock or Google adapters]
    Context --> Renderer[Validated document generators]
    API --> DB[(Owned SQLite records)]
    Approval --> DB
    Renderer --> Files[(Private atomic artifacts)]
```

The runtime remains one backend process. Package boundaries organize implementation; the MCP arrows remain real network calls. Stdio is available through the host CLI as a separate transport.
