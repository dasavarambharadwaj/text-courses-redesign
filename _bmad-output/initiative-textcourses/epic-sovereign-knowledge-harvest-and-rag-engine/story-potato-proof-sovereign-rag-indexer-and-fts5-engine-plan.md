# Story 4: Potato-Proof Sovereign RAG Indexer & SQLite FTS5 Point Retrieval

**Status**: completed  
**Covers**: FR-45.1, FR-45.3, FR-45.4, FR-45.5, FR-45.6, FR-45.7, FR-45.8, FR-45.9, AD-12  
**Prerequisites**: Story 2  

## Context & Objectives
Build a sovereign, zero-API, local knowledge indexer spearheaded by **📚 Denis Diderot (The Master Synthesizer & Encyclopedist)** capable of indexing 50MB to 1GB of heterogeneous research sources on potato-tier hardware (e.g. ThinkPad T480, 8GB RAM, Intel 8th-Gen CPU, zero GPU/NPU):
- Peak RAM consumption strictly stays below 50MB during both indexing and retrieval.
- Pure Python standard library implementation using `sqlite3` with FTS5 and Porter stemmer.
- Zero external vector databases, background daemons, or cloud API keys.
- Deterministic 5-stage validation pipeline: Gate 0 (Dynamic auto-bypass if empty/below threshold), Gate 1 (Scan & SHA-256 across all formats and arbitrary folder depths), Gate 2 (Hierarchical breadcrumb chunking with parent folder preservation), Gate 3 (SQLite FTS5 DB, `catalog.json`, and `manifest.json` generation inside dedicated `rag-db/`), Gate 4 (Automated probe verification).
- Sub-15ms BM25 hybrid search with contextual snippet highlighting.
- High-visibility console search inspection printing query, latency, and matching excerpts.
- Incremental course-correction diff tracking with audit events in `manifest.json["history"]`.
- Universal multi-format ingestion (source code across all major languages, Jupyter notebooks, transcripts, structured data, documentation) with strict binary/lockfile exclusion.

## Implementation Steps
1. Create `_tc/scripts/indexer.py` with:
   - `init_index_db()`: Initializes WAL mode, memory cache, `documents`, `chunks`, and `fts_chunks` FTS5 virtual table with Porter stemmer.
   - `parse_source_file_into_chunks()`: Dispatches specialized chunkers for markdown, code, notebooks (`.ipynb`), transcripts (`.vtt`, `.srt`), and structured data (`.csv`, `.json`).
   - `get_base_breadcrumbs()`: Preserves full directory hierarchies (`[TopFolder > Subfolder > ... > File.ext]`).
   - `run_build_index()`: Executes Gates 0–4, populating `rag-db/index.db`, `rag-db/catalog.json`, and `rag-db/manifest.json`.
   - `run_query_index()`: Fast BM25 hybrid point retrieval with snippet highlighting and live console observability.
2. Wire `indexer.py` into unified dispatcher `tc.py` (`tc index build`, `tc index query`, `tc index catalog`, `tc index manifest`).
3. Create dedicated skill `skills/tc-index/SKILL.md` (Denis Diderot) and metadata files `bmod.toml`, `customize.toml`.
4. Mirror runtime copies to `skills/tc-init/scripts/runtime/` and `skills/tc-index/scripts/`.
5. Verify with comprehensive unit tests in `tests/test_indexer.py`.
