---
name: tc-index
description: "Potato-proof sovereign knowledge indexer and cross-source catalog synthesizer led by Denis Diderot. Indexes 50MB to 1GB of sources locally via SQLite FTS5 and synthesizes catalog.json with zero external APIs."
---

# `tc-index`: Potato-Proof Sovereign Knowledge Indexer & Cross-Source Synthesizer

`tc-index` is the local, zero-API knowledge synthesis and point-retrieval engine spearheaded by **📚 Denis Diderot (The Master Synthesizer & Encyclopedist)**. It indexes heterogeneous materials in `research/<slug>/sources/` (downloaded textbooks, cloned GitHub repos, lecture transcripts) into a sovereign SQLite FTS5 database (`index.db`) and synthesizes a unified canonical domain taxonomy (`catalog.json`) **with zero cloud dependencies and zero external API calls**.

By extracting high-consensus topics, vocabulary, and code identifiers across all harvested literature, `tc-index` guarantees that `/tc-create` synthesizes **ONE single, master, comprehensive curriculum** rather than naively mirroring any individual textbook's table of contents.

---

## Core Invariants

1. **Potato-Proof Hardware Profile (<50MB RAM Ceiling) (FR-45.1)**:
   - Designed to run smoothly on legacy hardware (e.g., ThinkPad T480, 8GB RAM, Intel 8th-Gen CPU, zero GPU/NPU).
   - Powered entirely by Python standard library `sqlite3` using FTS5 (Full-Text Search 5) with Porter stemming.
   - Zero heavyweight machine-learning daemons, zero PyTorch/Transformers overhead, zero memory leaks. Peak RAM footprint strictly stays below 50MB even with 1GB of text.
2. **Unified Curriculum Invariant (FR-45.2)**:
   - The system must **never** generate courses by naive book mirroring ("Book A Chapter 1, Book B Chapter 1").
   - Instead, `tc-index` generates `catalog.json`, synthesizing cross-source topic frequency rankings, consensus scores, and prerequisite dependencies.
   - `/tc-create` consumes `catalog.json` to build one unified, deduplicated syllabus covering 100% of the corpus.
3. **Sovereign Point Retrieval (<15ms Latency) (FR-45.3)**:
   - Evaluates search queries using BM25 ranking and highlights matching contextual snippets.
   - Sub-15ms local query latency on commodity laptop hardware.
4. **Autonomous 5-Gate Pipeline with Deterministic Validation (FR-45.4)**:
   - **Gate 0: Auto-Bypass**: Automatically skips indexing when `sources/` contains zero files or falls below minimum word threshold, eliminating empty database overhead.
   - **Gate 1: Scan**: Enumerate and hash all candidate files across arbitrarily deep directories, accurately classifying them into source code, notebooks, transcripts, structured data, and documentation.
   - **Gate 2: Chunk**: Semantic breadcrumb chunking (300–600 words) preserving full directory parent trails (`[TopFolder > Subfolder > ... > File.ext > Section/Symbol]`).
   - **Gate 3: Index**: Write to sovereign `index.db` in WAL mode and atomically emit `catalog.json` and `manifest.json`.
   - **Gate 4: Verify**: Execute automated probe query to validate retrieval latency (<15ms) and recall.
5. **Zero User-Installation Burden (FR-45.5)**:
   - Relies exclusively on standard library modules (`sqlite3`, `hashlib`, `json`, `re`, `pathlib`).
   - No external vector databases, no Docker containers, no background services.
6. **Live Console Observability & Ground Truth Verification**:
   - Any RAG query prints transparent diagnostic search inspection into the console displaying the exact input query, latency, and retrieved excerpts with BM25 scores.
7. **Deep Hierarchical Directory Traversal & Universal Multi-Format Support (FR-45.9)**:
   - Traverses nested folder structures to arbitrary depths without truncating parent directory names.
   - Ingests all technical formats: source code (`.py`, `.rs`, `.go`, `.ts`, `.js`, `.c`, `.cpp`, `.h`, `.java`, `.kt`, `.cs`, `.sh`, `.sql`), notebooks (`.ipynb`), subtitles/transcripts (`.vtt`, `.srt`), structured data (`.json`, `.toml`, `.yaml`, `.csv`, `.tsv`, `.xml`, `.proto`), and documentation (`.md`, `.txt`, `.rst`, `.adoc`, `.tex`).
   - Strictly ignores non-text binaries, lockfiles, and build directories (`.git`, `node_modules`, `__pycache__`, `target`).

---

## Conventions

- `{project-root}` is the nearest folder containing `_tc/` or `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (`skills/tc-index`).
- Per-course sovereign RAG database, domain catalog, and sources manifest live in:
  - `{project-root}/courses/<slug>/rag-db/index.db` (also mirrored at `research/<slug>/rag-db/index.db`)
  - `{project-root}/courses/<slug>/rag-db/catalog.json`
  - `{project-root}/courses/<slug>/rag-db/manifest.json`

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/indexer.py` exists.
- If not found: TextCourses is not initialized in this workspace. Run `/tc-init` first.

---

## Workflow

### 1. Build Sovereign Index & Synthesize Domain Catalog

After harvesting research materials with `/tc-research` (or when adding new files during course correction):

```bash
uv run _tc/scripts/tc.py index build --slug <course-slug>
```

Or via direct script:
```bash
uv run _tc/scripts/indexer.py build --slug <course-slug>
```

**Output in `rag-db/`**:
- `rag-db/index.db`: Sovereign SQLite FTS5 database with document metadata, breadcrumb chunks, and full-text search indexes.
- `rag-db/catalog.json`: Deduplicated master domain taxonomy containing ranked consensus topics, code identifiers, and prerequisite vocabulary.
- `rag-db/manifest.json`: Complete audit trail tracking all source files used in RAG creation (paths, SHA-256, sizes, chunk counts, timestamps, and course correction change history).

### 2. Fast Point Retrieval & Verification Probe

Execute sub-15ms BM25 hybrid search across all harvested textbooks and lecture transcripts:

```bash
uv run _tc/scripts/tc.py index query --slug <course-slug> --query "consensus state machine" --top-k 5
```

Returns structured JSON containing:
- `chunk_id`, `source_title`, `source_type`, `breadcrumb`
- `bm25_score`
- `highlighted_snippet` (with `<b>` matches)
- `latency_ms`

### 3. Inspect Synthesized Catalog

Review the domain taxonomy that feeds into `/tc-create`:

```bash
uv run _tc/scripts/tc.py index catalog --slug <course-slug> --json
```

---

## Integration with `/tc-create`

When `/tc-create` executes the Adversarial Triad Consensus Dialectic:
1. It automatically detects `research/<slug>/sources/catalog.json`.
2. **Denis Diderot** enters the faculty deliberation panel, verifying that the proposed curriculum weaves together theory from textbooks, implementation from open repos, and mental models from lecture transcripts.
3. High-consensus canonical topics populate chapter and section outlines, guaranteeing non-mirroring master synthesis.
