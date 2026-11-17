# Remote server integration boundary

The runtime mounts five trusted package-owned servers. Assertions are private host credentials. Public MCP OAuth discovery, arbitrary hosted-server registration and third-party schema onboarding are deferred.

The independent client can address a trusted HTTP(S) base URL and requires HTTPS outside loopback. This does not establish a public remote MCP service. Exposure, consent, tenancy and capability distribution need separate review.

A future integration must define owner/authentication, transport, audience, tool permissions, reviewed schema/policy digest, metadata-read permissions, deadlines and isolation. Descriptions and remote schemas are untrusted. No current example configuration activates such a server.

Use the [local client guide](client-integration.md) and [observed compatibility](compatibility-matrix.md) for supported behavior.
