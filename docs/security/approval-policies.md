# Exact-action approvals

Every Google write requires explicit review, including drafts, labels, Calendar changes, folders and uploads. Local generation requires an authorized request and owner/quota checks.

The proposal binds user, Google account, canonical tool, normalized arguments, target/content snapshot, expiration and run. Uploads also bind the owned artifact checksum. The UI shows destinations, recipients, attendees, content and changes. The model never receives an executable capability.

The server validates capability, binding, expiry, digest and fresh provider snapshot. Approval consumption, executable-run validation and durable operation creation stay in one transaction, followed by dispatch.

Draft sends use approved MIME with stale-content detection. Calendar updates preserve conditional revisions. Reads may retry within bounds; dispatched non-idempotent writes do not retry automatically. Dispatch uncertainty retains outcome_unknown.

Rejection, expiration, changed actions, cross-user use and replay cannot authorize a write. Connector disable removes local authority; grant revocation invalidates affected grants/capabilities. Reconnection/restart cannot consume authority again.

These invariants are covered by approval, protocol and recovery tests. Prior results are baseline evidence; final workspace results belong in the [handoff](../verification/final-handoff.md). Actual Google writes remain NOT_RUN without controlled targets and explicit authorization.
