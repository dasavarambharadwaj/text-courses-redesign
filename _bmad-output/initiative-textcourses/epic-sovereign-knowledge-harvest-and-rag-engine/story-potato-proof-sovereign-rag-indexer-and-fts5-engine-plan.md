# Story 4: Potato-Proof Sovereign RAG Indexer & SQLite FTS5 Point Retrieval

**Status**: completed  
**Covers**: FR-45.1, FR-45.3, FR-45.4, FR-45.5, AD-12  
**Prerequisites**: Story 2  

## Context & Objectives
Build a sovereign, zero-API, local knowledge indexer spearheaded by **📚 Denis Diderot (The Master Synthesizer & Encyclopedist)** capable of indexing 50MB to 1GB of heterogeneous research sources on potato-tier hardware (e.g. ThinkPad T480, 8GB RAM, Intel 8th-Gen CPU, zero GPU/NPU):
- Peak RAM consumption strictly stays below 50MB during both indexing and retrieval.
- Pure Python standard library implementation using `sqlite3` with FTS5 and Porter stemmer.
- Zero external vector databases, background daemons, or cloud API keys.
- Deterministic 4-stage validation pipeline: Gate 1 (Scan & SHA-256), Gate 2 (Breadcrumb Chunking), Gate 3 (SQLite FTS5 DB & Catalog Synthesis), Gate 4 (Automated Probe Verification).
- Sub-15ms BM25 hybrid search with contextual snippet highlighting.

## Implementation Steps
1. Create `_tc/scripts/indexer.py` with:
   - `init_index_db()`: Initializes WAL mode, memory cache, `documents`, `chunks`, and `fts_chunks` FTS5 virtual table with Porter stemmer.
   - `parse_markdown_into_breadcrumb_chunks()`: Semantic 400–800 word chunking with full heading hierarchy preservation.
   - `run_build_index()`: Executes Gates 1–4, creating `research/<slug>/sources/index.db`.
   - `run_query_index()`: Fast BM25 hybrid point retrieval with snippet highlighting.
2. Wire `indexer.py` into unified dispatcher `tc.py` (`tc index build`, `tc index query`, `tc index catalog`).
3. Create dedicated skill `skills/tc-index/SKILL.md` (Denis Diderot) and metadata files `bmod.toml`, `customize.toml`.
4. Mirror runtime copies to `skills/tc-init/scripts/runtime/` and `skills/tc-index/scripts/`.
5. Verify with comprehensive unit tests in `tests/test_indexer.py`.
