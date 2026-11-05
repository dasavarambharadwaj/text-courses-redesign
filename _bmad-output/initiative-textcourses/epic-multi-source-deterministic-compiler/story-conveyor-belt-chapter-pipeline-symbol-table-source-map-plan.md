---
title: 'Conveyor-Belt Chapter Pipeline & Symbol Table (source-map.toml)'
type: 'feature'
ticket: '3'
created: '2026-11-02'
status: done
baseline_revision: '852bbb6df446c6912573e727090574f93fd40976'
route: 'oneshot'
route_source: 'auto'
risk: 'high'
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

**Problem:** Large textbooks (500+ pages) exceed LLM context windows if ingested all at once, leading to context rot and loss of earlier sections. Furthermore, runtime probabilistic chunk retrieval suffers from retrieval misses and high latency.

**Approach:** Implement `_tc/scripts/source_mapper.py` with:
1. `split_source_into_conveyor_batches` bounding token volume strictly below 25k tokens per batch with running vocabulary accumulation.
2. `compile_source_map` generating `courses/<slug>/source-map.toml` matching the companion schema with dialectic synthesis across multi-source overlaps.
3. `read_source_pointer` providing $O(1)$ sub-5ms exact verbatim line slices.
4. Auto-compilation hook in `course_builder.py` upon course scaffolding.

## Boundaries & Constraints

**Always:**
- Keep batch token loads bounded below 25,000 tokens during conveyor-belt ingestion.
- Pre-map 100% of curriculum concepts to exact source line spans `[line_start, line_end]` and verbatim anchors.
- Flag multi-source concept intersections with `dialectic = true` and actionable synthesis notes.
- Strictly adhere to Zero-BMad invariant across scripts and test suites.

**Never:**
- Never invoke runtime vector databases or probabilistic chunk searching for syllabus lesson delivery.
- Never lose source line numbering or heading context during mapping.

## Verification Evidence

- 5/5 unit tests passed in `tests/test_source_mapper.py`.
- Runtime scripts verified in `_tc/scripts/source_mapper.py`, `skills/tc-init/scripts/runtime/source_mapper.py`, and `skills/tc-create/scripts/source_mapper.py`.

</intent-contract>
