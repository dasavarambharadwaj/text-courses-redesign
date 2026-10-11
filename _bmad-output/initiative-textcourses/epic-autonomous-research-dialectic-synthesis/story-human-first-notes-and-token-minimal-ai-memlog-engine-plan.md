---
title: "Human-First Notes & Token-Minimal AI Memlog Engine"
type: "feature"
ticket: 4
created: "2026-10-11"
status: "done"
baseline_revision: "92a1e16"
route: "oneshot"
route_source: "auto"
risk: "medium"
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

**Problem:** Previously, compiled textbook notes and memory logs mixed linguistic registers. Notes contained prompt meta-artifacts or excessive jargon without intuitive human analogies, while memlog entries could be overly verbose, wasting valuable context window tokens for AI models. Furthermore, interaction tracing was incomplete: learner questions, diagnostic misconceptions, and lesson advancement were not consistently mirrored into the course pedagogical memlog.

**Approach:** Enforce strict dual-register linguistic separation across TextCourses:
1. **Human-First Notes (`notes/chapter-XX.md` & `section/notes.md`)**: Written strictly for human comprehension in simple, intuitive English with clear analogies, step-by-step mechanical breakdowns, concrete code, common traps, and attribution to the active teacher persona.
2. **AI-First Memlog (`courses/<slug>/memlog.md`)**: Written strictly for AI models using ultra-dense, token-minimal key-value notation conveying complete semantic state with minimum token footprint.
3. **Closed Tracing Loop**: `teach_engine.py` logs taught concepts and learner questions to `memlog.md`. `diagnostic_tester.py` mirrors misconceptions and milestone achievements directly to `memlog.md`.

</frozen-after-approval>

## Implementation Notes

Completed oneshot implementation of FR-32 Human-First Textbook Notes vs AI-First Token-Minimal Memlog Engine across notes_compiler.py, teach_engine.py, diagnostic_tester.py, memlog.py, and skill files.

## Review Triage Log

- quick-lens: Verified human-first plain English notes formatting with analogies and teacher attribution; verified token-minimal key-value AI memlog notation in courses/<slug>/memlog.md; verified closed conversation tracing in teach_engine and diagnostic_tester; zero BMad references; unit tests pass.
