# MeetLens — Customer Pilot One-Pager

## Problem
Technical architecture and design-review meetings collect more questions than there is time to ask. Repeated and overlapping questions consume moderator attention, while less popular but important questions can be buried.

## What MeetLens does
MeetLens turns distributed participant questions into:

**raw questions → semantic intents → diverse nominees → explainable priority → moderator decision → asked question → outcome**

It is not a meeting summarizer. The product is designed around question intelligence and human-controlled moderation.

## Pilot hypothesis
MeetLens can reduce semantic redundancy, preserve participant coverage, and reduce the moderator's question-triage effort.

## Controlled pre-pilot evidence
Three synthetic technical-review scenarios, 20 questions total, were evaluated with the deterministic offline fallback.

- Mean pairwise cluster F1: **1.0000**
- Mean semantic compression rate: **0.5000**
- Mean nominees per intent: **2.0**
- All scenarios ran offline

**Important:** these are controlled fixture results, not customer validation. The fixtures are intentionally small and should be replaced/expanded during the external pilot.

## What the customer pilot measures
1. Moderator triage time.
2. Moderator acceptance rate.
3. Moderator edit rate.
4. Duplicate suppression.
5. Participant coverage.
6. Number of questions actually asked.
7. Answer/usefulness outcomes.

## Privacy boundary
The MVP is designed local-first. Participant identity can be minimized in shared views, meeting data can be deleted, and the moderator remains the final decision maker. Production deployment still requires full authentication, tenant isolation, secure transport/storage, retention policy enforcement, and security/privacy review.

## Pilot ask
Run MeetLens in **three real technical architecture/design-review meetings** with one designated moderator and compare it against the team's normal question-triage process.

## The success question
**Does MeetLens let a meeting moderator get from many questions to a smaller, more representative set of high-value questions faster and with better confidence than the team's current process?**
