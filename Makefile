export UV_CACHE_DIR ?= /tmp/workspace-ai-uv-cache
export PATH := $(CURDIR)/.local/tools/pnpm/node_modules/.bin:$(PATH)
API_URL ?= http://127.0.0.1:8000
PY_DIRS := apps/api mcp-servers packages/mcp-common evaluations/src tests scripts examples conftest.py
PY_SOURCES := apps/api/src mcp-servers/gmail/src mcp-servers/calendar/src mcp-servers/drive/src mcp-servers/documents/src mcp-servers/google-docs/src mcp-servers/sheets/src mcp-servers/slides/src mcp-servers/demo/src packages/mcp-common/src evaluations/src
COVERAGE := $(foreach source,$(PY_SOURCES),--cov=$(source))
.PHONY: setup dev lint format format-check typecheck schema-check architecture-check test test-unit test-integration test-e2e smoke security dependency-audit eval ci build seed-demo reset-demo
setup:
	uv sync --locked --all-packages
	uv run --locked python scripts/bootstrap_pnpm.py
	pnpm install --frozen-lockfile
dev:
	uv run --locked workspace-ai dev
lint:
	uv run --locked ruff check $(PY_DIRS)
	pnpm lint
format:
	uv run --locked ruff check --select I --fix $(PY_DIRS)
	uv run --locked ruff format $(PY_DIRS)
format-check:
	uv run --locked ruff check --select I $(PY_DIRS)
	uv run --locked ruff format --check $(PY_DIRS)
	pnpm format-check
	pnpm --filter @mcp-workspace/web exec prettier --check ../../packages/shared-types/src/index.ts ../../packages/shared-types/package.json ../../packages/shared-types/tsconfig.json
typecheck:
	uv run --locked mypy $(PY_SOURCES) scripts examples
	pnpm typecheck
schema-check:
	uv run --locked python scripts/check_schema.py
	pnpm check:api
	uv run --locked python scripts/export_tool_policies.py --check
architecture-check:
	uv run --locked python scripts/check_architecture.py
	node scripts/check_frontend_architecture.mjs
test:
	mkdir -p .local
	uv run --locked pytest $(COVERAGE) --cov-fail-under=86 --cov-report=term-missing --cov-report=json:.local/coverage.json
	pnpm test
test-unit:
	uv run --locked pytest apps/api/tests/unit mcp-servers/documents/tests/unit packages/mcp-common/tests/unit
test-integration:
	uv run --locked pytest tests apps/api/tests/contract apps/api/tests/security
test-e2e:
	uv run --locked python scripts/run_e2e.py
smoke:
	uv run --locked workspace-ai smoke --url $(API_URL)
security: dependency-audit
	uv run --locked bandit -q -r $(PY_SOURCES) -x apps/api/src/mcp_workspace_api/db/migrations
	uv run --locked pytest tests/security apps/api/tests/security
	uv run --locked python scripts/secret_scan.py
dependency-audit:
	mkdir -p .local
	uv export --locked --all-packages --format requirements-txt --no-emit-workspace --output-file .local/audit-requirements.txt >/dev/null
	uv run --locked pip-audit --strict --disable-pip --no-deps -r .local/audit-requirements.txt
	pnpm audit --audit-level=high
eval:
	uv run --locked workspace-ai eval --url $(API_URL)
build:
	uv build --all-packages
	pnpm build
ci: lint format-check typecheck schema-check architecture-check test security build test-e2e
seed-demo:
	uv run --locked workspace-ai seed-demo
reset-demo:
	uv run --locked workspace-ai reset-demo
