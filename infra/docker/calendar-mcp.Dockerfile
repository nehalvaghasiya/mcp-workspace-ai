ARG BASE_IMAGE=mcp-workspace-ai:base
FROM ${BASE_IMAGE}
HEALTHCHECK NONE
CMD ["workspace-ai", "mcp", "calendar", "--transport", "stdio"]
