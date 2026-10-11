---
title: "Root-Level Research Substrate & Workspace Transparency"
type: "feature"
ticket: 1
created: "2026-10-11"
status: "done"
baseline_revision: "92a1e16"
route: "oneshot"
route_source: "auto"
risk: "low"
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

**Problem:** Learners opening a bootstrapped TextCourses workspace lack an immediate orientation guide explaining what each folder (`courses/`, `profile/`, `roadmap/`, `portfolio/`, `_tc/`) represents, and research dossiers are obscured in internal directories rather than accessible at the root alongside courses.

**Approach:** Update `bootstrapper.py` to scaffold a visible root-level `research/` directory on workspace initialization and automatically deploy a welcoming, human-navigable `WORKSPACE_GUIDE.md` (and root `README.md` if absent) describing every directory's purpose, file types, and primary slash commands.

</frozen-after-approval>

## Implementation Notes

Completed oneshot implementation of FR-33 Root-Level Research Substrate & Workspace Transparency.

## Review Triage Log

- quick-lens: Verified research/ and sources/ directory scaffolding; verified WORKSPACE_GUIDE.md deployment and directory indexing; zero BMad references; unit tests pass.
