---
title: 'Complete Coverage Verification Ledger (coverage-ledger.md)'
type: 'feature'
ticket: '4'
created: '2026-11-02'
status: done
baseline_revision: '852bbb6df446c6912573e727090574f93fd40976'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran:
  - 'quick'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '_tc/INTERACTION_STANDARDS.md'
  - '_bmad-output/initiative-textcourses/spec-multi-source-compiler/spec-multi-source-compiler.md'
  - '_bmad-output/initiative-textcourses/spec-multi-source-compiler/source-map-schema.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** In typical RAG or AI curriculum generation, portions of source material are arbitrarily dropped without notice, leaving learners with blind spots.

**Approach:** Implement `audit_coverage` in `_tc/scripts/auditor.py` and CLI subcommand `coverage` that cross-references all source chapter/section headings against the curriculum and `source-map.toml`, emits `courses/<slug>/coverage-ledger.md` with an exact parity audit matrix, and fails validation if any source section was dropped.

## Boundaries & Constraints

**Always:**
- Extract all headings (chapters, sections, subsections) from all peer source books.
- Audit source-to-curriculum parity mathematically (100.0% coverage required to pass).
- Emit a clean markdown audit matrix at `courses/<slug>/coverage-ledger.md`.
- Adhere strictly to the Zero-BMad invariant across scripts and test suites.

**Never:**
- Never silently drop or ignore sections from uploaded source books.
- Never pass pre-flight validation if unmapped source sections exist.

## Verification Evidence

- 4/4 unit tests passed in `tests/test_coverage_auditor.py`.
- Runtime scripts verified in `_tc/scripts/auditor.py`, `skills/tc-init/scripts/runtime/auditor.py`, and `skills/tc-verify-course/scripts/auditor.py`.

</intent-contract>
