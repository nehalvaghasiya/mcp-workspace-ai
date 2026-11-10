ARG BASE_IMAGE=mcp-workspace-ai:base
FROM ${BASE_IMAGE}
CMD ["uvicorn", "mcp_workspace_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
