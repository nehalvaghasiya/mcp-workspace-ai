# Using the workspace

Choose **Explore demo** to create an isolated synthetic workspace. Its clock is fixed at November 5, 2026 in America/Chicago so “tomorrow” and weekday examples remain reproducible. The mock banner and FakeLLM label distinguish this from live data.

Try: “Review Northstar launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports.” The assistant searches through real MCP endpoints, lists sources and produces files in Artifacts. The demo model follows curated routines; it is not general-purpose language understanding. A configured real model is used only in live mode with explicit data-sharing consent.

Expand the tool timeline for actual calls and errors. Sources point to returned records; synthetic records may not have live URLs. MCP Explorer shows discovered servers, schemas, risk classifications and protocol metadata. Connector switches change callable permissions.

For a follow-up email, use “Send a launch email to alex@example.invalid.” Creating the draft first requires approval. Sending requires a second approval of the exact draft content. Rejecting leaves that action unexecuted. Approvals expire after five minutes; edited or stale targets need a fresh proposal. Duplicate approval clicks cannot dispatch a second write.

Conversation history and files persist through restart. Reopening a stream does not resend the prompt. Cancel stops future steps and attempts to stop current work; a write already submitted to a provider may have an unknown outcome. Inspect the provider before proposing it again.

Download files to inspect them in Office-compatible software. PDF/Office structural validation is separate from native visual review. Excel formulas are stored but are not calculated on the server. HTML is downloaded as an attachment. The browser never receives OAuth tokens.

Delete a conversation to remove its local derived files and state. Delete account data in Settings to erase that user's local data and attempt Google grant revocation. This does not delete Google-side resources. To reconnect a live account, follow the [Google setup guide](../security/oauth-setup.md).
