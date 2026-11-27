FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /usr/local/bin/uv
USER vscode
# The editor starts and stops development services on demand.
HEALTHCHECK NONE
