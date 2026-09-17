# MeetLens — First External Evaluation Package

## Purpose

This is the smallest practical package for the first independent human evaluator. The evaluator is testing the product thesis, not the polish of a commercial SaaS.

**Thesis under test:** MeetLens can turn many participant questions into a smaller, diverse, moderator-approved question portfolio that is more useful than simple popularity triage.

## Moderator protocol

1. Create one technical architecture/design-review meeting.
2. Add 4–8 participants with short role/expertise descriptions.
3. Ask every participant to submit 2–4 questions independently, without viewing other participants' submissions.
4. Run processing.
5. Review the generated categories and at least two nominees per category.
6. For each of the five highest-priority categories, choose one action: approve, edit, or reject.
7. Record which approved questions were actually asked.
8. Record whether each asked question received a useful answer and rate usefulness 1–5.
9. Export the evidence report.
10. Repeat for three meetings before drawing product conclusions.

## Participant instructions

Submit the questions you would genuinely want answered in the meeting. Do not try to help the AI by wording questions similarly to other participants. Do not include secrets or personal data in the pilot corpus.

## Blind evaluation questions

Each evaluator answers these without seeing benchmark results first:

- How many questions did you submit?
- How many distinct information needs did you believe you had?
- How many categories produced by MeetLens felt genuinely distinct?
- Did the nominated questions preserve your important concerns?
- Did MeetLens surface a concern you would probably have missed in a popularity-only queue?
- How much time did moderation take compared with manually triaging the raw queue?
- For each approved question: approve / edit / reject.
- Overall moderator usefulness: 1–5.
- Would you use this in another meeting of the same type? yes / no / unsure.

## Success criteria for the pilot

The product should not be called validated unless independent humans report measurable value. A strong early signal is:

- most high-priority nominees are approved or lightly edited;
- materially fewer questions need manual triage;
- moderators report that intent-level grouping preserves important coverage;
- at least one meeting reveals a useful concern that popularity-only ordering would likely have buried;
- the workflow is faster or clearer than the moderator's existing process.

No numerical threshold is treated as universal; the pilot is primarily for discovering whether the workflow changes real behavior.

## Privacy boundary for the MVP pilot

Use synthetic or non-sensitive questions. Collect only what is needed for the evaluation. Participant submissions remain participant-scoped in the MVP UI; moderator evidence is the broader view. Production deployments still require stronger authentication, tenant isolation, encrypted storage, retention enforcement, and legal review.
