# Coding standards and ownership

Define at most one handwritten class per file, including Python models, dataclasses, protocols, exceptions and nested test helpers. Keep one React component per component file and one handwritten TypeScript class per file. Related pure functions may share a focused module. Target fewer than 300 lines; split or document justified exceptions above 400.

Generated contracts, data and unchanged migration revisions have enumerated size exceptions. Do not create empty classes or hide ordinary source behind exemptions.

API imports servers/common; servers import common only; common imports neither applications nor servers. Web consumes generated shared types, never the reverse. Architecture checks include lazy imports and nested class definitions.

Server packages own tool schema/risk/scope definitions; the API assembles them. Generated schema/type/policy documents are projections. Preserve validation, defaults, schema titles and request envelopes when extracting classes.

Keep process-wide tasks/adapters/locks/render limits/deletion fences together. Preserve atomic approval consumption and operation creation. Provider calls stay inside real MCP handlers with downstream checks.

Use typed boundaries, explicit errors, bounded resources and sanitized logs. Retrieved text is evidence, not instructions. Load installed resources without checkout-parent assumptions. Manage dependencies with uv/pnpm and avoid unrelated upgrades during structural work.
