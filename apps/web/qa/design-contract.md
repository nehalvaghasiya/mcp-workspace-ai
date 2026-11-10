# Workspace UI contract

Purpose: inspect evidence, coordinate work across connected tools, and explicitly review exact external actions. Primary action is sending a chat request; tool execution and sources remain visible alongside the answer.

Audience: an individual developer or portfolio evaluator repeatedly scanning conversations and protocol activity. Tone: quiet, precise productivity software. Distinctive detail: a fine vertical activity rail connects individual MCP calls to their measured outcomes. Local references: product requirements §3 and §FR-09, demonstration specification §8.

Hierarchy: workspace navigation → conversation → response/source evidence → visible tool activity. Target viewports: 390x844 and 1440x900, with a minimum usable width of 375px. Use system typography, warm white surfaces, ink text, restrained teal status, and amber for approval holds. Navigation collapses on narrow screens; the timeline becomes a separate panel toggle. Focus rings, textual status, 44px touch targets, reduced-motion support, and semantic headings are required.

States: loading shows stable placeholders; empty chat offers concrete prompts; request failure shows a retry control; partial results preserve messages and disclose run failure; success displays sourced answers and validated downloads; permission states show connect controls or exact approval details. Offline status persists until connectivity returns. Demo labels remain visible throughout synthetic sessions.
