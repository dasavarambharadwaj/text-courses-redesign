---
title: "Autonomous 5-Hat Deep Research Engine (scout.py & tc-research)"
type: "feature"
ticket: 2
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

**Problem:** Researching a new course previously produced minimal machine-only digests in hidden directories (`.tc/research/`), lacking deep synthesis, multi-perspective critical evaluation, and visible access for learners and downstream tools. Learners were confused about what `tc-research` was for.

**Approach:** Re-architect `scout.py` and `skills/tc-research/SKILL.md` as the Autonomous 5-Hat Deep Research Engine led by 🔬 Marie Curie. Multi-round searches and scraped documentation are stress-tested through 5 critical hats (Industry Practitioner, Academic Purist, Beginner Friction Hunter, Edge-Case Systems Engineer, Modern Ecosystem Reviewer) using tree-of-thought exploration, outputting comprehensive visible dossiers (`dossier.md`, `five-hats-critique.md`, `sources.json`) in `research/<topic-slug>/` for direct consumption by `tc-create`.

</frozen-after-approval>

## Implementation Notes

Completed oneshot implementation of FR-30 Autonomous 5-Hat Deep Research Engine in scout.py and tc-research.

## Review Triage Log

- quick-lens: Verified 5-hat critical reflection (Industry, Academic, Beginner, Edge-Case, Modern Ecosystem); verified tree-of-thought exploration branches; verified visible research/<slug>/ placement (dossier.md, five-hats-critique.md, sources.json, digest.json); zero BMad references; unit tests pass.
