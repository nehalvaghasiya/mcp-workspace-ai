# Reproducible demonstration

Run `make setup` and `make dev`, open http://localhost:5173, and choose **Explore demo**. All mail, meetings, recipients and files are synthetic. The fixture clock is November 5, 2026 in America/Chicago. FakeLLM implements curated routines; it is not a general-purpose language model.

## Five-minute walkthrough

1. Ask “Summarize unread launch emails from the last week.” Inspect Gmail calls and source cards.
2. Ask “What do I have tomorrow afternoon?” Then ask for “3 meeting slots next Wednesday.” Inspect explicit dates/timezone and the absence of bookings.
3. Ask “Find my project proposal in Drive and summarize the risks.” Open its source and read trace.
4. Ask “Review Northstar launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports.” Download the four files and inspect all four server namespaces in activity.
5. In a new conversation, ask “Draft a reply to alex@example.com with launch decisions.” Inspect exact recipient and body; reject it to demonstrate zero writes, then submit again and approve draft creation. “Send that draft now” requires a separate approval of the MIME snapshot.
6. Visit Artifacts, Connectors, Settings, and MCP Explorer. Reload the report conversation to show persisted history. Live connection buttons require explicit operator Google setup.

## Workflow acceptance mapping

| PRD workflow | Demonstration / verification |
|---|---|
| W01 unread launch summary | Gmail search/get, bounded source-grounded answer; evaluation Gmail cases |
| W02 tomorrow afternoon | Frozen-clock date/daypart and timezone tests |
| W03 proposal risks | Drive search/read with per-file access and citations |
| W04 three slots | Free/busy results converted to suggestions, no create event |
| W05 draft reply | Resolve thread/context and recipient; exact draft approval |
| W06 send draft | Separate send approval; exact approved MIME, one dispatch |
| W07 thread PDF | Thread read and valid PDF artifact |
| W08 email tracker | Typed XLSX cells, task owners and source references |
| W09 five-slide proposal | Drive read and valid five-slide PPTX |
| W10 recap and Drive/email | Multi-step calendar/report/upload/draft/send; each Google write pauses separately |
| W11 embedded injection | Hostile source is data; policy prevents unauthorized writes; security/API tests |
| W12 tool availability | Actual registry discovery and MCP Explorer |
| W13 reschedule | Ambiguous “3” asks for clarification; explicit time preserves selected date/duration and requires approval |
| W14 four formats | Same retrieved evidence rendered into DOCX/PDF/XLSX/PPTX; actual backend browser test |

For W10 use an explicit synthetic recipient, for example “Check my next meetings and email a recap to alex@example.com, save it to Drive.” Continue only after reviewing each proposed action. Missing recipients and ambiguous references are allowed to request clarification.

Fault demonstrations: disable a connector and retry a read; reject an action; cancel an active run; reload a finished conversation. Source IDs and partial completed traces remain inspectable. Restarting the process marks active work interrupted; it never silently resends an external action.

The preserved baseline [generated examples](../examples/document-generation/generated) and [protocol evidence](../docs/verification/historical/core-protocol-proof.md) are actual synthetic output. The [evaluation report](../docs/evaluations/evaluation-guide.md) records measured denominators and limits.
