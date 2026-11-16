# Agent workflows

The agent executes bounded typed steps with persisted results, position, contextual references and pending actions. FakeLLM implements curated synthetic routines. A configurable real provider requires separate per-user consent to the configured provider/model destination.

Each step resolves authorized context, validates arguments and crosses the official MCP client. A Google write prepares a snapshot-bound proposal and pauses. Approval resumes that exact action; each later write requires its own approval.

Traces contain statuses, durations, source references and operation IDs, excluding raw bodies and credentials. Answers and evidence remain private conversation data. Generated files retain their source provenance.

Persisted SSE IDs support reconnection without resubmission. Duplicate request IDs return existing runs or reject conflicting content. Cancellation prevents future steps and attempts to stop active work; already dispatched writes retain their actual or uncertain outcome.

Deletion waits for renderer cleanup and fences late refresh/generation responses. The [walkthrough](../../demo/walkthrough.md) maps W01–W14. [Evaluation methodology](../evaluations/evaluation-guide.md) distinguishes pipeline assertions from real-model quality.
