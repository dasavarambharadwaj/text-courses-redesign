---
title: 'Grounded Sensei Runtime Grounding & Vocabulary Contract Gate'
type: 'feature'
ticket: '5'
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
  - '_bmad-output/initiative-textcourses/spec-multi-source-compiler/vocabulary-contract.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** Learners are easily overwhelmed by unearned technical jargon that appears without prior intuition, and multi-source differences often confuse students when textbooks use competing terminology for the same underlying mechanism.

**Approach:** Upgrade `_tc/scripts/teach_engine.py` with:
1. Grounded Sensei $O(1)$ runtime symbol table lookup from `source-map.toml` with dialectic synthesis across multi-source intersections.
2. Vocabulary contract enforcement accumulating approved terms from completed course history and providing intuition-before-label guidance for the active target primitive.
3. `verify_vocabulary_turn` validator and CLI `verify-vocab` subcommand detecting unearned technical jargon.

## Boundaries & Constraints

**Always:**
- Separate textbook substance from teacher tone; teacher delivers in empathetic, everyday plain English regardless of textbook density.
- Load verbatim source slices via $O(1)$ deterministic symbol table reads.
- Restrict technical vocabulary to approved antecedent terms and the designated target term.
- Enforce the Zero-BMad invariant across scripts and tests.

**Never:**
- Never dump unearned technical jargon without antecedent intuition.
- Never use vector chunk searches when `source-map.toml` is compiled.

## Verification Evidence

- 5/5 unit tests passed in `tests/test_teach_grounded_sensei.py`.
- 7/7 regression tests passed in `tests/test_teach_engine.py`.
- Runtime scripts verified in `_tc/scripts/teach_engine.py`, `skills/tc-init/scripts/runtime/teach_engine.py`, and `skills/tc-teach/scripts/teach_engine.py`.

</intent-contract>
