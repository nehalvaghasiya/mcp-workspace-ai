ARG BASE_IMAGE=mcp-workspace-ai:base
FROM ${BASE_IMAGE}
USER 10001:10001
HEALTHCHECK NONE
CMD ["workspace-ai", "mcp", "gmail", "--transport", "stdio"]
