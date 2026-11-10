# syntax=docker/dockerfile:1
ARG NODE_IMAGE=node:24-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

FROM ${NODE_IMAGE} AS web-build
WORKDIR /app
RUN npm install --global --no-audit --no-fund pnpm@12.18.0
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared-types/package.json ./packages/shared-types/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web/ ./apps/web/
COPY packages/shared-types/ ./packages/shared-types/
RUN pnpm --filter @mcp-workspace/web build

FROM ${PYTHON_IMAGE} AS python-build
COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock .python-version LICENSE ./
COPY apps/api/ ./apps/api/
COPY mcp-servers/ ./mcp-servers/
COPY packages/mcp-common/ ./packages/mcp-common/
COPY evaluations/ ./evaluations/
RUN uv sync --locked --all-packages --no-dev --no-editable

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    MODE=mock \
    LLM_PROVIDER=fake \
    DATA_DIR=/app/.local \
    API_URL=http://127.0.0.1:8000 \
    WEB_ORIGIN=http://localhost:8000 \
    WEB_DIST_DIR=/app/apps/web/dist
WORKDIR /app
RUN groupadd --gid 10001 workspace \
    && useradd --uid 10001 --gid workspace --create-home --shell /usr/sbin/nologin workspace \
    && install -d -o 10001 -g 10001 -m 0700 /app/.local
COPY --from=python-build /app/.venv /app/.venv
COPY --from=web-build /app/apps/web/dist ./apps/web/dist
COPY LICENSE ./LICENSE
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=4 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ready', timeout=3).read()"]

FROM runtime AS api
CMD ["uvicorn", "mcp_workspace_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
