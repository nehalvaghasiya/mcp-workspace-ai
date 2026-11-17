# Observed MCP tool catalog

These 31 schemas were discovered from the pre-reorganization mock servers using the official MCP client. The reorganization preserves their raw schemas and policy digests; fresh runtime evidence is recorded in the verification handoff. Input is wrapped as `{"request": {...}}`; full schemas are in tool-catalog.json. Google writes remain approval-gated even when enabled in discovery.

| Tool | Risk | Required live scope suffixes | Approval |
|---|---|---|---|
| gmail.search_messages | READ | gmail.readonly | no |
| gmail.get_message | READ | gmail.readonly | no |
| gmail.get_thread | READ | gmail.readonly | no |
| gmail.list_labels | READ | gmail.readonly | no |
| gmail.create_draft | ACCOUNT_WRITE | gmail.compose | yes |
| gmail.send_draft | EXTERNAL_EFFECT | gmail.compose | yes |
| gmail.apply_labels | ACCOUNT_WRITE | gmail.modify | yes |
| calendar.list_calendars | READ | calendar.calendarlist.readonly | no |
| calendar.list_events | READ | calendar.events.readonly | no |
| calendar.get_event | READ | calendar.events.readonly | no |
| calendar.query_freebusy | READ | calendar.freebusy | no |
| calendar.create_event | EXTERNAL_EFFECT | calendar.events | yes |
| calendar.update_event | EXTERNAL_EFFECT | calendar.events | yes |
| calendar.cancel_event | DESTRUCTIVE | calendar.events | yes |
| drive.search_files | READ | drive.file | no |
| drive.get_file_metadata | READ | drive.file | no |
| drive.read_file | READ | drive.file | no |
| drive.list_folder | READ | drive.file | no |
| drive.upload_artifact | ACCOUNT_WRITE | drive.file | yes |
| drive.create_folder | ACCOUNT_WRITE | drive.file | yes |
| artifact.create_docx | LOCAL_WRITE | app ownership | no |
| artifact.create_pdf | LOCAL_WRITE | app ownership | no |
| artifact.create_xlsx | LOCAL_WRITE | app ownership | no |
| artifact.create_pptx | LOCAL_WRITE | app ownership | no |
| artifact.create_csv | LOCAL_WRITE | app ownership | no |
| artifact.create_markdown | LOCAL_WRITE | app ownership | no |
| artifact.create_html | LOCAL_WRITE | app ownership | no |
| artifact.get_artifact_metadata | READ | app ownership | no |
| artifact.validate_artifact | READ | app ownership | no |
| artifact.list_artifacts | READ | app ownership | no |
| demo.ping | READ | app ownership | no |

Each server also exposes `workspace://<server>/templates` and the `meeting_brief` prompt. No credentials or private provider bodies appear in these resources.

Artifact tools use the same bounded IR. Their format field must match the selected create_* tool. Unsupported remote sharing/overwrite/delete tools are not registered and are denied.
