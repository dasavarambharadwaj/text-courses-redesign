# Epic 10: Autonomous Multi-Source Harvester, AI-Era Research & Potato-Proof Sovereign RAG Indexer

**Initiative**: `initiative-textcourses`  
**Slug**: `epic-sovereign-knowledge-harvest-and-rag-engine`  
**Status**: completed  
**Covers**: FR-42, FR-43, FR-44, FR-45, AD-9, AD-10, AD-11, AD-12, AD-13  

## Executive Summary
This epic implements the end-to-end sovereign knowledge acquisition, cognitive pacing, and potato-proof local RAG pipeline:

1. **Universal Zero-Cognitive-Overload Pacing & Centralized Interaction Standards (`FR-42`, `AD-9`)**:
   - Enforces the strict single-question-per-turn invariant across all skills to eliminate cognitive burden.
   - Standardizes language to a 10-year-old Plain English baseline, eliminating complex pedagogical jargon.
   - Expands learner roles to 10 diverse backgrounds (lawyer, doctor, accountant, designer, etc.) with dynamic recommendation badges.
   - Condenses teacher personas down to 3 intuitive archetypes (Feynman, Socrates, Turing).
   - Establishes `_tc/INTERACTION_STANDARDS.md` as the centralized source of truth.

2. **Autonomous Multi-Source Deep Harvester & Community Consensus Sourcing (`FR-43`, `AD-10`)**:
   - Discovers undisputed community consensus gold-standard textbooks, canonical guides, and landmark lectures from Reddit (e.g. `r/learnprogramming`, `r/rust`), Hacker News, and university syllabi.
   - Implements automated GitHub repository and markdown textbook cloning into `research/<slug>/sources/repos/<repo_name>/`.
   - Extracts and cleans landmark YouTube video lecture subtitles/transcripts via `harvest-youtube` into `research/<slug>/sources/transcripts/`.
   - Introduces a graceful acquisition gate for commercial/proprietary books in `research/<slug>/gold-standards.md`.

3. **Mandatory AI-Era Research Grounding & Dedicated AI-Pro Hat Engine (`FR-44`, `AD-11`)**:
   - Systematically investigates how the AI era transforms the target discipline (automated boilerplate vs. core architecture).
   - Integrates modern AI-adjacent tools, APIs, models, and hallucination defense guardrails into `dossier.md` and `digest.json`.
   - Adds the `ai_pro_strategist` critical lens to the Universal Hat Registry in `scout.py` (accessible via `--ai` flag or `--hats ai_pro`).

4. **Potato-Proof Sovereign RAG Indexer & SQLite FTS5 Point Retrieval (`FR-45.1`, `FR-45.3`, `FR-45.4`, `FR-45.5`, `AD-12`)**:
   - Builds a 100% local, zero-API, zero-daemon search and indexing engine in `_tc/scripts/indexer.py` led by Denis Diderot.
   - Enforces a strict `<50MB RAM` ceiling using standard library `sqlite3` FTS5 with Porter stemming, running seamlessly on legacy hardware (e.g., ThinkPad T480 with 8GB RAM).
   - Operates across 4 deterministic validation gates: Gate 1 (Scan & SHA-256), Gate 2 (Breadcrumb Chunking), Gate 3 (SQLite FTS5 DB & Catalog Synthesis), Gate 4 (Automated Probe Verification).
   - Delivers sub-15ms BM25 hybrid search with contextual snippet highlighting.

5. **Cross-Source Knowledge Taxonomy Synthesis & Non-Mirroring Curriculum (`FR-45.2`, `AD-13`)**:
   - Synthesizes `research/<slug>/sources/catalog.json` containing cross-source deduplicated canonical topics, consensus scores, code identifiers, and prerequisite vocabulary.
   - Integrates with `/tc-create` (`course_builder.py`) so Daedalus drafts ONE unified master course covering 100% of the ingested material without naively mirroring any single book's table of contents.
   - Denis Diderot joins the faculty Triad consensus panel, casting an affirmative vote when non-mirroring cross-source synthesis is satisfied.

## Stories Breakdown
1. `story-low-cognitive-load-interaction-standards-plan.md` (FR-42, AD-9)
2. `story-multi-source-deep-harvester-and-gold-standards-plan.md` (FR-43, AD-10)
3. `story-ai-era-research-grounding-and-ai-pro-hat-plan.md` (FR-44, AD-11)
4. `story-potato-proof-sovereign-rag-indexer-and-fts5-engine-plan.md` (FR-45.1, FR-45.3, FR-45.4, FR-45.5, AD-12)
5. `story-cross-source-catalog-synthesis-and-non-mirroring-curriculum-plan.md` (FR-45.2, AD-13)
