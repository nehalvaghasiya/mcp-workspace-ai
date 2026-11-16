# Google sign-in and connector setup

No Google setup is needed for the mock demo. The live code is tested with mocked HTTP; use a dedicated controlled account for actual integration checks.

1. Create a Google Cloud project and enable Gmail, Calendar and Drive APIs. Configure the consent audience, permitted test users, scopes and application branding. Native Docs/Sheets/Slides content is exported through Drive in the core implementation.
2. Create a Web application OAuth client. Register the exact callback used by `GOOGLE_REDIRECT_URI`, initially `http://localhost:8000/api/auth/google/callback`. Use the same browser hostname for the app, API callback and cookies; do not mix localhost and 127.0.0.1.
3. Copy `.env.example` to an ignored `.env`. Set `MODE=live`, client ID/secret, stable `SESSION_SECRET`, and `TOKEN_ENCRYPTION_KEY`. Generate a key with `uv run python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`. Store it privately; losing it makes existing credentials unreadable.
4. Sign in with Google for app identity. In Connectors, request reads separately. Use the write-permission link only when those tools are needed. The application enables only methods authorized by the actually returned grants.
5. Configure a server-side OpenAI-compatible provider/model/key, review that provider's data terms, then authorize live-content sharing in the app settings. This consent is separate from Google login.
6. Run controlled read-only checks first. Test write proposals only against controlled resources and recipients, approving each exact action in the UI. Real sends, invitations and remote changes are not part of default tests.

## Scope mapping

| Feature | Scope |
|---|---|
| Sign-in | openid, email, profile |
| Gmail reads | gmail.readonly |
| Draft creation/send | gmail.compose |
| Applying message labels | gmail.modify; gmail.labels is insufficient |
| Calendar list | calendar.calendarlist.readonly |
| Event details/free-busy | calendar.events.readonly and calendar.freebusy |
| Calendar writes | calendar.events |
| App-created/selected Drive files | drive.file |
| Optional Drive Open-with menu | drive.install in addition to drive.file |

Gmail reading/composition and broad Drive scopes have verification implications. This core release does not silently request broad Drive access. Missing or narrower scopes disable the affected tools. Google Testing-mode refresh expiry or revocation requires reconnecting.

## Existing Drive files

`drive.file` does not authorize searching the entire Drive. Localhost can upload and read app-created files. To open existing files, configure Drive UI integration with a fully qualified Open URL ending `/api/auth/google/drive-open`, the Importing option/MIME types as appropriate, and drive.install consent. Google does not accept localhost as that Open URL. Domain setup and live verification are external requirements; no public deployment is performed automatically.

The callback handles ids/exportIds and bounded resource keys. It never uses Drive's supplied userId as app identity; metadata permission checks cross MCP under the active app session. JS Picker is intentionally omitted because it requires a browser access token.

Disabling a connector preserves the account grant locally. “Disconnect Google” attempts project-grant revocation and removes all affected local credentials. Google-side generated files/events/messages are not deleted by local account cleanup.

Official sources: [web-server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server), [OIDC](https://developers.google.com/identity/openid-connect/openid-connect), [Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth), [Drive UI configuration](https://developers.google.com/workspace/drive/api/guides/enable-sdk).
