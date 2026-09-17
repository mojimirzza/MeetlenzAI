# MeetLens Customer Pilot Protocol

## Objective
Test whether MeetLens improves question triage in a real technical architecture/design-review meeting.

## Control condition
The team uses its normal/manual process for one comparable meeting or one defined segment.

## Treatment condition
MeetLens receives participant questions, clusters them semantically, generates nominees, ranks categories, and exposes them to the moderator for approval/edit/rejection.

## Minimum pilot
- 3 meetings
- 5–25 participants per meeting
- same or comparable meeting type
- one designated moderator
- explicit consent for the pilot and data handling

## Primary metrics
1. Moderator time spent triaging questions.
2. Moderator acceptance rate of nominees.
3. Moderator edit rate.
4. Duplicate/near-duplicate suppression.
5. Participant coverage across selected intents.
6. Number of questions actually asked.
7. Answer/usefulness rate.

## Guardrails
- Human moderator remains final authority.
- No autonomous question asking.
- No cloud transmission unless explicitly enabled.
- Participant identity is minimized in shared views.
- Meeting data has a defined retention/deletion policy.

## Success gate
Proceed toward production hardening only if at least three real meetings show consistent moderator trust and a measurable reduction in manual triage effort.

## Evidence package generated per meeting
- raw question count
- intent/cluster map
- nominees
- priority explanations
- moderator decisions
- asked questions
- outcomes
- audit trail
- timing metrics
- model/prompt versions

## What counts as external evidence?
A meeting conducted with participants who are not the development team, with their informed participation and normal meeting stakes. Synthetic or founder-only demos remain pre-pilot evidence.
