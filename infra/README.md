# Local build and runtime

The default Compose stack runs one nonroot backend process with five independently addressable MCP endpoints and the built frontend. It preserves private persistent storage and publishes only loopback port 8000.

```sh
docker compose -f docker-compose.yml up --build --wait
docker compose -f docker-compose.yml exec -T workspace workspace-ai smoke
```

Stop it with `docker compose -f docker-compose.yml down`. Keep the named volume for normal local use; deleting it removes app-owned data. Mock mode needs no Google account, model key or GPU.

`docker/base.Dockerfile` is the shared build source. It installs all eight Python workspace members non-editably through the root uv lock and builds the web workspace through the pinned pnpm lock. Fonts, templates and migrations come from installed packages. The final image is nonroot; Compose uses a read-only root filesystem, dropped capabilities, bounded PIDs and temporary scratch space.

## Diagnostic component images

Build the common base first, then select a thin entrypoint:

```sh
docker buildx build --load --target runtime -f infra/docker/base.Dockerfile -t mcp-workspace-ai:base .
docker buildx build --load -f infra/docker/api.Dockerfile -t mcp-workspace-ai:api .
docker buildx build --load -f infra/docker/demo-mcp.Dockerfile -t mcp-workspace-ai:demo .
```

The Gmail, Calendar, Drive, Documents and Demo wrappers run the existing `workspace-ai mcp <server> --transport stdio` command. Documents keeps the wire name `artifact`. They require the same private assertion and authorized local context as the normal CLI; no credentials are bundled into images. Use controlled temporary storage and private environment configuration when exercising them. Do not put tokens in command arguments or captured output.

The web wrapper is a static-asset preview on port 8080 using Python's HTTP server; it is diagnostic, not the complete authenticated application or a production reverse proxy. Normal browser use is the default API container serving assets and `/api` together.

These optional images do not change the supported single-process topology or claim a distributed/multiworker deployment. Terraform, Nginx and monitoring folders contain explicit roadmap notes because those integrations remain deferred.

## CI and development

The workflows separate quality/package builds, security checks, real MCP integration, browser workflows and deterministic evaluations. All use mock mode with Google/model credentials cleared. The manual release workflow builds downloadable files and an image archive; it never publishes a release or pushes an image.

The devcontainer installs Python 3.12, uv 0.12.1 and Node 24, then calls `make setup` for the project-local pnpm bootstrap and locked dependencies. Its configuration is separate from the smaller runtime image. No remote CI run, devcontainer startup or public deployment is implied by these files; executed results belong in the verification handoff.

Dependabot uses the supported root uv workspace and npm/pnpm manifests. See [uv's Dependabot guidance](https://docs.astral.sh/uv/guides/integration/dependabot/) and the [Node devcontainer feature](https://github.com/devcontainers/features/tree/main/src/node) for configuration references.
