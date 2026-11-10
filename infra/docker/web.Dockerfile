ARG BASE_IMAGE=mcp-workspace-ai:base
FROM ${BASE_IMAGE}
HEALTHCHECK NONE
EXPOSE 8080
CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", "/app/apps/web/dist"]
