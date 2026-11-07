# Gmail workflows

Ask “Summarize unread launch emails from the last week.” Inspect gmail.search_messages and subsequent message/thread reads with source references.

Ask “Draft a reply to alex@example.com with launch decisions.” Review the recipient, subject and body before approving gmail.create_draft. “Send that draft now” requires a separate gmail.send_draft approval, bound to the MIME snapshot. Rejecting, changing or replaying authority cannot send mail.

The mock account and recipients are synthetic. Live execution requires configured consent/scopes, controlled recipients and separate authorization. See the [approval policy](../../docs/security/approval-policies.md).
