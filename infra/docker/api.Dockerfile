ARG BASE_IMAGE=mcp-workspace-ai:base
FROM ${BASE_IMAGE}
USER 10001:10001
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=4 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ready', timeout=3).read()"]
CMD ["uvicorn", "mcp_workspace_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
