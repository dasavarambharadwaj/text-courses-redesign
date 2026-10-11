---
title: "Adversarial Triad Consensus Dialectic with Live Fact-Checking (course_builder.py & tc-create)"
type: "feature"
ticket: 3
created: "2026-10-11"
status: "done"
baseline_revision: "92a1e16"
route: "oneshot"
route_source: "auto"
risk: "high"
review: "quick"
review_source: "pinned"
lenses_ran: ["quick-lens"]
review_loop_iteration: 1
context:
  - "_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md"
  - "_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md"
  - "_bmad-output/initiative-textcourses/epic-autonomous-research-dialectic-synthesis/epic-autonomous-research-dialectic-synthesis.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The previous Triad Consensus implementation was a mechanical check that did not engage in authentic adversarial argumentation or live fact-checking between Daedalus, Marie, and Hypatia. Courses were generated without real debate, without checking online documentation, without addressing gaps left by the broad research dossier, and without tailoring to learner preferences.

**Approach:** Upgrade `course_builder.py` and `skills/tc-create/SKILL.md` to conduct a genuine multi-round adversarial debate between distinct personas:
1. Daedalus (Curriculum Architect): Ingests the pre-course research dossier (`research/<slug>/dossier.md` or `digest.json`) and personalizes the curriculum based on learner intent (`profile/preferences.md`). He identifies any gaps or advanced topics missed by the research dossier and injects them to ensure complete coverage.
2. Marie (Empirical Investigator & Fact-Checker): Critiques proposals, verifies APIs, and performs simulated/live web search queries to validate claims, flagging deprecated methods or missing industry invariants.
3. Hypatia (Logic & Prerequisite Auditor): Audits conceptual dependencies, prerequisite DAG ordering, cognitive leaps, and vocabulary contracts, rejecting any lesson introducing ungrounded terms.
Deliberations continue until unanimous consensus is achieved. Transcripts are saved to `courses/<slug>/consensus-deliberation.md` and appended to `_tc/cache/consensus-trace.jsonl`.

</frozen-after-approval>

## Implementation Notes

Completed oneshot implementation of FR-31 Adversarial Triad Consensus Dialectic with live fact-checking, gap bridging, and deliberation transcript generation in course_builder.py and tc-create skill.

## Review Triage Log

- quick-lens: Verified 3 distinct hats (Daedalus, Marie, Hypatia); verified live fact-checking online queries; verified consensus-deliberation.md generation and structured trace in _tc/cache/consensus-trace.jsonl; verified gap topic personalization based on profile/preferences.md; zero BMad references; unit tests pass.
