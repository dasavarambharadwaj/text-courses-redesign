---
title: 'Macro Semantic TOC Alignment & Deduplication Engine (toc_aligner.py)'
type: 'feature'
ticket: '2'
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
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** When a user provides multiple peer books covering the same domain (e.g. DDIA and Database Internals), concepts like LSM-Trees or B-Trees are covered in both. Without macro TOC alignment, the course either duplicates concepts or arbitrarily drops one book's perspective.

**Approach:** Build `_tc/scripts/toc_aligner.py` to extract heading hierarchies (`#`, `##`, `###`), normalize topic keys using canonical synonym clusters, classify topics as common (overlap) or niche (unique to one source), flag dialectic potential for overlapping topics, and produce a unified topological curriculum DAG.

## Boundaries & Constraints

**Always:**
- Treat all sources as co-equal peers; no book is an anchor that subsumes another.
- Preserve 100% of niche sections unique to any source.
- Flag overlapping topics with `dialectic_potential = true` and multiple source occurrences.
- Follow strict Zero-BMad invariant across scripts and tests.

**Never:**
- Never discard unique topics from any peer source.
- Never teach a concept twice; multi-source topics appear exactly once in the curriculum DAG.

## Verification Evidence

- 5/5 tests passing in `tests/test_toc_aligner.py`.
- Runtime script verified in `_tc/scripts/toc_aligner.py` and `skills/tc-init/scripts/runtime/toc_aligner.py`.

</intent-contract>
