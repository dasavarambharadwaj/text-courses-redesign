# Story 5: Cross-Source Domain Catalog Synthesis & Unified Master Curriculum

**Status**: completed  
**Covers**: FR-45.2, AD-13  
**Prerequisites**: Story 4  

## Context & Objectives
Ensure that harvested research materials are synthesized into ONE master curriculum rather than naively mirroring any single book's table of contents ("Book A Chapter 1, Book B Chapter 1"):
- Synthesize `research/<slug>/sources/catalog.json` containing cross-source consensus topics, mention frequencies, code identifiers, and prerequisite vocabulary.
- Integrate `catalog.json` into `/tc-create` (`_tc/scripts/course_builder.py`):
  - Injects canonical consensus topics and prerequisite terms into `generate_archetype_chapters()`.
  - Enriches autonomous multi-path brainstorming in `brainstorm_curriculum_paths()`.
  - Integrates Denis Diderot into the Triad Consensus Dialectic panel.
  - Registers `catalog.json` and `index.db` into `course.toml` sources.

## Implementation Steps
1. In `_tc/scripts/indexer.py`:
   - Implement `extract_domain_catalog()` to extract consensus topics, source coverage counts, and prerequisite vocabulary terms into `catalog.json`.
2. In `_tc/scripts/course_builder.py`:
   - Detect `research/<slug>/sources/catalog.json` in `run_triad_consensus_loop()`.
   - Pass catalog data to `brainstorm_curriculum_paths()`, `generate_archetype_chapters()`, and `generate_triad_deliberation()`.
   - Add Denis Diderot to deliberation panel and append consensus vote.
   - Record `catalog.json` and `index.db` in `course.toml` sources.
3. Mirror updated `course_builder.py` to `skills/tc-init/scripts/runtime/` and `skills/tc-create/scripts/`.
4. Verify with automated integration tests in `tests/test_indexer.py` (`test_course_builder_integrates_catalog_synthesis`).
