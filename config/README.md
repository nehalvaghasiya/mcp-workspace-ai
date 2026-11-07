# Configuration ownership

Environment variables remain the runtime authority. Server/model files are operator examples. Tool policies are a generated JSON-compatible YAML projection of the typed Python registry; regenerate with `uv run python scripts/export_tool_policies.py` and check with `make schema-check`. Logging is an optional standard-library dictConfig template, not loaded automatically. Evaluation YAML describes the frozen dataset; dataset records and runner assertions remain authoritative. Never place real credentials in these files.
