# Synthetic example prompts

Use **Explore demo** after `make dev`. The demo clock is frozen; Google writes below affect only synthetic state in mock mode.

1. Summarize unread emails from the last week about launch.
2. What do I have tomorrow afternoon?
3. Find my project proposal in Drive and summarize the risks.
4. Give me 3 meeting slots next Wednesday.
5. Draft a reply to alex@example.com with the launch decisions.
6. Send that draft now. (Use after approving draft creation; review the separate send approval.)
7. Make a PDF summary of this thread.
8. Create an Excel tracker from these project emails.
9. Build a five-slide presentation from the proposal.
10. Check my next meetings and email a recap to alex@example.com, save it to Drive.
11. What tools are available and which server exposes them?
12. Review Northstar launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports.

Follow-up references require prior conversation context. Missing recipients and ambiguous meeting references ask for clarification. The malicious-instruction fixture is tested as retrieved data; the host never treats its embedded instruction as approval.
