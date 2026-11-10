# Deterministic evaluation

Run `make eval` against a running mock API, or `workspace-ai eval --url http://127.0.0.1:8000` from an installed environment. The runner measures 52 preserved synthetic cases using FakeLLM. These results measure the fixture pipeline, not general model reasoning.

The six datasets have one authoritative copy in `src/mcp_workspace_evaluations/datasets`, packaged with the runner. `datasets` links to that directory for convenient repository access. Source distributions explicitly include the package directory so both direct wheels and wheels rebuilt from source contain the same cases.

| Dataset | Cases |
|---|---:|
| tool_selection.jsonl | 26 |
| multi_step_workflows.jsonl | 8 |
| document_generation.jsonl | 8 |
| authorization.jsonl | 5 |
| prompt_injection.jsonl | 1 |
| ambiguity_and_errors.jsonl | 4 |

Focused runners in `runners` select tools, workflows, security or artifact cases and report their actual denominators. The separate adversarial pytest suite is not counted as additional deterministic evaluation cases. Fresh measurements go in `reports/latest.json` and `reports/latest.md`; earlier evidence remains in `reports/historical`.
