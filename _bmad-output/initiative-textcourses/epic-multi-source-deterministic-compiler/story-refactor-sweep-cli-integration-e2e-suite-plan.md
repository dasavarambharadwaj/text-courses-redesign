---
title: 'Refactor Sweep, CLI Integration & Multi-Source End-to-End Test Suite'
type: 'feature'
ticket: '6'
created: '2026-11-02'
status: done
baseline_revision: '852bbb6df446c6912573e727090574f93fd40976'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran:
  - 'quick'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '_tc/INTERACTION_STANDARDS.md'
  - '_bmad-output/initiative-textcourses/spec-multi-source-compiler/spec-multi-source-compiler.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** Individual components of the Multi-Source Deterministic Compiler need to be integrated into user-facing skills (`tc-research`, `tc-create`, `tc-teach`, `tc-verify-course`), deprecated legacy runtime vector search references cleaned up, and the entire multi-source lifecycle validated end-to-end with zero regressions.

**Approach:**
1. Update skill instructions across `skills/tc-create`, `skills/tc-research`, `skills/tc-teach`, and `skills/tc-verify-course`.
2. Construct comprehensive integration test `tests/test_multi_source_e2e.py` demonstrating the full lifecycle from multi-book extraction, deduplicated DAG alignment, conveyor-belt batching, symbol table compilation, complete coverage ledger verification, to Grounded Sensei lesson delivery.
3. Validate strict Zero-BMad invariant across all scripts and skills.
4. Verify 100% test pass rate across the full 296-test suite.

## Boundaries & Constraints

**Always:**
- Ensure all 6 spec capabilities (`CAP-1` to `CAP-6`) are verified in the end-to-end suite.
- Maintain 100% backwards compatibility with existing courses and runtime scripts.
- Enforce the Zero-BMad invariant across all runtime files and skill documentation.

**Never:**
- Never break existing course directories or test fixtures.
- Never re-introduce runtime vector search dependencies into syllabus lesson paths.

## Verification Evidence

- 2/2 tests passed in `tests/test_multi_source_e2e.py`.
- 296/296 tests passed across entire repository test suite.
- Zero-BMad invariant verified across all scripts and skills.

</intent-contract>
