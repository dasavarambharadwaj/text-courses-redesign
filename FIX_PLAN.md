# TextCourses: Deterministic Compiler Architecture & Full Engineering Fix Plan

**Date**: 2026-11-05  
**Target Repository**: `C:\Users\dasav\Documents\Code\text-courses-redesign`  
**Reference Broken Output**: `C:\Users\dasav\Documents\Courses\software architecture`  
**Core Directive**: **NO RUNTIME RAG. Zero vector search, zero fuzzy chunking.** TextCourses operates strictly as a **Multi-Source Deterministic Compiler** with $O(1)$ Pedagogical Symbol Table (`source-map.toml`) line lookups and complete-coverage verification (`coverage-ledger.md`).

---

## 1. Executive Summary & Why the System Broke

### 1.1 The User's Real Grievance
When the user ran `tc` on *"Software Architecture: OS Primitives, Computer Networks, and Authentication Models"*:
1. **The research step found zero books, zero papers, and zero official RFCs**. It fell back to generating a fake 3-line topic placeholder in `scout.py` (`# Topic\nOverview...\n## Core Concepts...`).
2. **The engine never searched for or downloaded materials**. It didn't fetch RFC 8446 (TLS 1.3), RFC 9113 (HTTP/2), RFC 9000 (QUIC), RFC 6749 (OAuth 2.0), Linux `epoll(7)` man pages, arXiv papers, or identify landmark textbooks like Tanenbaum (*Modern Operating Systems*) or Stevens (*TCP/IP Illustrated*).
3. **The engine never paused at Gate 1 (Material Acquisition Gate)** to say: *"Here are the landmark books and papers. I have auto-downloaded the official RFCs and specs. Drop your book PDF/EPUB or press [1] to proceed with open specs."*
4. Instead, it jumped straight into `course_builder.py`, generated fake "live fact-check" strings, and created an empty course scaffold without a single source mapped to it (`sources = []`).
5. **Folder chaos exploded**: `scout.py` wrote identical dummy files to **4 different folders** (`research/`, `sources/`, `_tc/research/`, `.tc/research/`), and `bootstrapper.py` created duplicate `plan/` vs `profile/` and `_tc/` vs `.tc/`.
6. **Git showed 71-142 phantom changes**: Windows NTFS directory junctions inside `skills/` broke git file tracking.

---

## 2. Core Architectural Philosophy: The Multi-Source Deterministic Compiler

TextCourses **strictly rejects runtime probabilistic RAG** (vector embeddings, fuzzy similarity, chunk fragmenting) for core curriculum delivery:
- Probabilistic chunk search slices code blocks and formulas in half, drops 10–20% of relevant passages through vocabulary mismatch, and destroys prerequisite sequence.
- **The Multi-Source Deterministic Compiler** acts as a true compiler:
  - **Pass 0 (Raw Extraction)**: `extractor.py` extracts pure text, code, and headings verbatim from PDFs, EPUBs, RFCs, and markdown with zero LLM rewriting.
  - **Pass 1 (Macro TOC Alignment)**: `toc_aligner.py` extracts Table of Contents ASTs, deduplicates overlapping primitives across peer books, and constructs a unified acyclic topological DAG.
  - **Pass 2 (Conveyor-Belt Ingestion)**: `source_mapper.py` sequentially processes sources chapter-by-chapter, generating:
    1. `courses/<slug>/.tc/source-map.toml` — The Pedagogical Symbol Table mapping 100% of curriculum concepts to exact source files, heading breadcrumbs, and verifiable line number spans.
    2. `courses/<slug>/.tc/coverage-ledger.md` — The Zero-Omission Audit Matrix mathematically proving 100.0% of source book chapters and sections are mapped.
  - **Pass 3 (Grounded Sensei Delivery)**: `teach_engine.py` retrieves source text via **deterministic $O(1)$ line-span slice lookup** from `source-map.toml`. Sub-millisecond retrieval, zero vector DB, zero hallucinations, zero unearned jargon.

```
                  RAW SOURCES
   (PDFs, EPUBs, Downloaded RFCs, ArXiv Papers, Cloned Repos)
                       │
                       ▼
            [Pass 0: Raw Ingestion]
            extractor.py (Verbatim text, zero rewriting)
                       │
                       ▼
          [Pass 1: Macro TOC Alignment]
          toc_aligner.py (Deduplicate shared topics across peer books)
                       │
                       ▼
       [Pass 2: Conveyor-Belt Ingestion]
       source_mapper.py (Chapter-bounded batch processing)
          ├── source-map.toml (O(1) concept-to-line-span symbol table)
          └── coverage-ledger.md (100% coverage audit proof)
                       │
                       ▼
        [Pass 3: Grounded Sensei Delivery]
        teach_engine.py (O(1) line-span lookup + Vocabulary Contract)
```

---

## 3. The Clean Canonical Filesystem Specification

### 3.1 Strict Workspace Layout
A TextCourses workspace MUST contain ONLY the following directories:

```
<Workspace-Root>/
├── profile/                         <- Learner Profile & Identity
│   ├── preferences.md               <- Active Teacher, Style, Role, Experience
│   └── memlog.md                    <- Global cross-course pedagogical memory
│
├── research/                        <- Domain Research Substrate (SINGLE DIRECTORY ONLY)
│   └── <course-slug>/               <- Research per topic
│       ├── gold-standards.md        <- Inventory of Books, Papers, RFCs & fetch status
│       ├── dossier.md               <- Deep synthesized technical dossier
│       ├── digest.json              <- Extracted symbols, vocabulary, prerequisites
│       ├── critique.md              <- Multi-hat dialectic critique
│       └── sources/                 <- REAL HARVESTED ASSETS
│           ├── papers/              <- Downloaded PDFs / TXT of research papers
│           ├── rfcs/                <- Downloaded IETF RFCs / W3C specs (.txt)
│           ├── repos/               <- Shallow-cloned open textbooks (e.g. rust-lang/book)
│           ├── transcripts/         <- Landmark lecture transcripts (.md)
│           ├── user-provided/       <- Books/PDFs dropped by user (.pdf, .epub)
│           └── sources-index.json   <- Cryptographic manifest of all harvested files
│
├── courses/                         <- Clean Human Canvas
│   └── <course-slug>/
│       ├── overview.md              <- Clean human-readable syllabus overview
│       ├── notes/                   <- Human-readable textbook notes compiled as taught
│       │   ├── chapter-01.md
│       │   └── chapter-02.md
│       └── .tc/                     <- ENCAPSULATED MACHINE SUBSTRATE (Hidden from learner)
│           ├── course.toml          <- Course manifest, DAG dependencies, section status
│           ├── memlog.md            <- Active working memory for AI tutor
│           ├── consensus-deliberation.md <- Triad consensus debate transcript
│           ├── curriculum-brainstorm.md  <- 4-paradigm pedagogical analysis
│           ├── source-map.toml      <- O(1) Pedagogical Symbol Table (line spans)
│           ├── coverage-ledger.md   <- Mathematical 100% source coverage audit proof
│           └── plans/               <- Internal AI lesson plans
│               └── chapter-01/
│                   └── sec-01/
│                       └── lesson-plan.md
│
├── portfolio/                       <- Applied proof-of-work capstone deliverables
│   └── <project-slug>/
│       ├── brief.md
│       └── review-report.md
│
├── roadmap/                         <- Multi-course prerequisite DAGs (optional)
│   ├── roadmap.toml
│   └── overview.md
│
└── _tc/                             <- Deterministic Runtime Engine (Single copy)
    ├── INTERACTION_STANDARDS.md
    ├── config.json
    └── scripts/                     <- Canonical Python runtime scripts
        ├── tc.py                    <- Unified dispatcher
        ├── scout.py                 <- Research scout
        ├── harvester.py             <- Multi-source asset harvester
        ├── paper_fetcher.py         <- NEW: IETF RFC, arXiv, and official doc auto-fetcher
        ├── book_scout.py            <- NEW: Google Books / OpenLibrary canonical search
        ├── extractor.py             <- Pure-Python verbatim document extraction
        ├── toc_aligner.py           <- Macro TOC deduplication & alignment
        ├── source_mapper.py         <- Conveyor-belt symbol table compiler
        ├── checkpoint_manager.py    <- Interactive Checkpoint Gates
        ├── course_builder.py        <- Triad consensus course scaffolder
        ├── teach_engine.py          <- Grounded Sensei $O(1)$ delivery
        ├── diagnostic_tester.py     <- Bloom taxonomy quiz engine
        ├── practical_evaluator.py   <- Hands-on capstone reviewer
        ├── notes_compiler.py        <- Clean textbook compiler
        └── auditor.py               <- Mathematical DAG & parity auditor
```

### 3.2 Strictly Forbidden Directories & Anti-Patterns
The following must **NEVER** be created:
- ❌ **`sources/` at workspace root**: All sources belong strictly inside `research/<slug>/sources/`.
- ❌ **`.tc/` at workspace root**: The runtime engine is `_tc/`. The `.tc/` directory exists ONLY inside `courses/<slug>/.tc/` to encapsulate course machine state.
- ❌ **`plan/` at workspace root**: Merged into `profile/`.
- ❌ **`_tc/research/` or `.tc/research/`**: Duplicate copies. Banned.
- ❌ **`agent/` or `.agents/` inside course workspaces**: Skills belong to the AI coding agent harness, not inside course directories.
- ❌ **`rag-db/` or vector database chunks**: Replaced entirely by `source-map.toml`.

---

## 4. The 4-Stage Research & Material Acquisition Pipeline

Before course compilation begins, `tc-research` must execute this exact sequential pipeline:

```
[User specifies Topic]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 1: CANONICAL DISCOVERY & CONSENSUS               │
│ - book_scout.py searches Google Books & OpenLibrary    │
│ - Names exact books with Authors, ISBNs, Editions      │
│ - Identifies landmark RFCs, specs, and arXiv papers    │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2: AUTONOMOUS ZERO-PROMPT AUTO-FETCH             │
│ - paper_fetcher.py downloads all IETF RFCs (text)      │
│ - paper_fetcher.py downloads open arXiv papers (PDF)   │
│ - harvester.py clones open GitHub textbook repos       │
│ - harvester.py extracts landmark lecture transcripts   │
│ - Saves everything into research/<slug>/sources/       │
└────────────────────────┬───────────────────────────────┘
                         │
         All Sources     │     Missing Proprietary
         Auto-Harvested? │     Landmark Textbooks?
         ┌───────────────┴───────────────┐
         ▼                               ▼
 ┌───────────────┐           ┌──────────────────────────────────────────┐
 │ Auto-Proceed  │           │ STAGE 3: INTERACTIVE MATERIAL GATE 1     │
 │ to Compile    │           │ Pauses and presents real inventory:      │
 └───────┬───────┘           │ - Downloaded RFCs & Papers ✅             │
         │                   │ - Proprietary Books Needed ⚠️            │
         │                   │ User Choice:                             │
         │                   │ [1] Proceed with Auto-Harvested Specs    │
         │                   │ [2] Pause & wait to drop PDF/EPUB        │
         │                   └────────────────────┬─────────────────────┘
         │                                        │ User dropped or picked 1
         └───────────────────┬────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 4: MULTI-SOURCE DETERMINISTIC COMPILATION        │
│ 1. extractor.py extracts raw text verbatim             │
│ 2. toc_aligner.py aligns TOCs & deduplicates topics    │
│ 3. course_builder.py builds unified DAG                │
│ 4. source_mapper.py compiles source-map.toml           │
│ 5. source_mapper.py compiles coverage-ledger.md        │
└────────────────────────────────────────────────────────┘
```

---

## 5. File-by-File Fix Blueprint

### 5.1 Implement `_tc/scripts/paper_fetcher.py`
Create `_tc/scripts/paper_fetcher.py` with zero external dependencies (standard library `urllib`, `json`, `re`, `pathlib`).

#### Core Responsibilities:
1. **IETF RFC Downloader**:
   - Maps standard protocol names to canonical RFC numbers:
     - `TLS 1.3` $\rightarrow$ RFC 8446
     - `HTTP/2` $\rightarrow$ RFC 9113
     - `HTTP/3` / `QUIC` $\rightarrow$ RFC 9000
     - `OAuth 2.0` $\rightarrow$ RFC 6749
     - `JWT` $\rightarrow$ RFC 7519
     - `TCP` $\rightarrow$ RFC 9293
     - `IP` $\rightarrow$ RFC 791
     - `WebSocket` $\rightarrow$ RFC 6455
   - Downloads plain text RFC directly from `https://www.rfc-editor.org/rfc/rfc{number}.txt`.
   - Saves to `research/<slug>/sources/rfcs/rfc{number}_{slug}.txt`.
2. **arXiv Paper Downloader**:
   - Queries `https://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=3`.
   - Downloads paper PDF from `https://arxiv.org/pdf/{arxiv_id}.pdf` directly into `research/<slug>/sources/papers/{arxiv_id}_{slug}.pdf`.
3. **Linux Kernel & Systems Documentation**:
   - For OS primitives (virtual memory, syscalls, epoll), fetches official manual pages from `man7.org` (e.g. `epoll(7)`, `mmap(2)`, `clone(2)`) and saves as clean text in `research/<slug>/sources/docs/`.

#### CLI Command:
```bash
uv run _tc/scripts/paper_fetcher.py fetch --slug <slug> --topic "<topic>" --workspace .
```

---

### 5.2 Implement `_tc/scripts/book_scout.py`
Create `_tc/scripts/book_scout.py` using standard library `urllib`, `json`, `re`.

#### Core Responsibilities:
1. **Google Books & OpenLibrary Canonical Discovery**:
   - Queries `https://www.googleapis.com/books/v1/volumes?q={query}&orderBy=relevance&maxResults=5` and `https://openlibrary.org/search.json?q={query}&limit=5`.
   - Returns real, canonical textbooks with:
     - Exact Title
     - Authors
     - Edition & Publication Year
     - ISBN-10 / ISBN-13
     - Pedagogical role / Why essential
2. **Open Textbook Repo Detection**:
   - Scans GitHub for canonical open textbooks (e.g. *OSTEP* `remzi-arpacidusseau/ostep-translations`, *TRPL* `rust-lang/book`, *Crafting Interpreters* `munificent/craftinginterpreters`).
   - If an open GitHub textbook is found, marks `status: "auto_fetchable"` and triggers `harvester.py harvest_github_repo`.
   - If proprietary/copyrighted (e.g. Tanenbaum's *Modern Operating Systems*, Stevens' *TCP/IP Illustrated*), marks `status: "acquisition_needed"`.

#### CLI Command:
```bash
uv run _tc/scripts/book_scout.py discover --slug <slug> --topic "<topic>" --workspace .
```

---

### 5.3 Fix `_tc/scripts/scout.py`
1. **Delete Lines 824–839 (Runaway Duplication)**:
   - Remove the loop writing to `ws / "sources" / slug`, `ws / "_tc" / "research" / slug`, and `ws / ".tc" / "research" / slug`.
   - Write exclusively to `research/<slug>/`:
     - `research/<slug>/gold-standards.md`
     - `research/<slug>/dossier.md`
     - `research/<slug>/digest.json`
     - `research/<slug>/critique.md`
     - `research/<slug>/sources/sources-index.json`
   - Delete `five-hats-critique.md` and `multi-hats-critique.md` duplicate filenames.
2. **Remove the 3-Line Mock Fallback (Lines 663–673)**:
   - Replace the mock `# Topic\nOverview...\n## Core Concepts` fallback:
     - Step 1: Call `book_scout.py` to identify gold-standard books.
     - Step 2: Call `paper_fetcher.py` to auto-download official RFCs, papers, and kernel docs.
     - Step 3: Call `harvester.py` to clone open textbook repos and fetch transcripts.
     - Step 4: Extract all harvested files in `research/<slug>/sources/` to form `extracted_content`.
     - Step 5: If zero sources are available, set `confidence = "unverified"` and block course scaffolding until sources are provided.

---

### 5.4 Fix `_tc/scripts/bootstrapper.py`
1. **Purge Duplicate Directories in `dirs_to_create` (Lines 435–455)**:
   - Only create:
     - `_tc/scripts`
     - `profile`
     - `research`
     - `courses`
     - `portfolio`
     - `roadmap`
   - **Do NOT create**: `_tc/research`, `.tc`, `plan`, `sources`, `plan/sources`.
2. **Single Config & Preferences**:
   - Write config ONLY to `_tc/config.json`.
   - Write preferences ONLY to `profile/preferences.md`.
   - Write memory ONLY to `profile/memlog.md`.

---

### 5.5 Fix `_tc/scripts/checkpoint_manager.py` & `tc.py`
1. **Enforce Material Acquisition Gate 1**:
   - Replace the dummy `rec_books = [f"Canonical reference for {topic_title}"]` (line 209 in `tc.py`).
   - Populate `recommended_books` with the real books discovered by `book_scout.py`.
   - List the auto-harvested RFCs and papers so the learner sees real progress:
     ```markdown
     📚 Gold Standard Material Identified:
     1. Modern Operating Systems (4th Ed) — Andrew S. Tanenbaum [ACQUISITION NEEDED]
     2. TCP/IP Illustrated, Vol. 1 (2nd Ed) — W. Richard Stevens [ACQUISITION NEEDED]
     3. Operating Systems: Three Easy Pieces (OSTEP) ✅ [AUTO-HARVESTED]
     4. RFC 8446 (TLS 1.3), RFC 9113 (HTTP/2), RFC 9000 (QUIC), RFC 6749 (OAuth 2.0) ✅ [AUTO-HARVESTED 4 SPECS]
     5. Linux epoll(7) & zero-copy manual pages ✅ [AUTO-HARVESTED]
     
     If you have a PDF or EPUB of the textbooks above, drop it into:
     research/<slug>/sources/user-provided/
     
     How would you like to proceed?
     - [1] (Recommended) Proceed with Auto-Harvested Official Specs & Open Texts
     - [2] Pause & Wait: I will drop my textbook files now
     ```
   - **Gate Invariant**: `course_builder.py` is blocked from running until the user selects `[1]` or drops a file.

---

### 5.6 Wire `source_mapper.py` & `coverage-ledger.md` into `course_builder.py`
1. **Remove Fake Fact-Checks (Lines 228–260 in `course_builder.py`)**:
   - Delete the hardcoded strings pretending to be "live fact-checks".
   - Ground the course directly in the harvested files in `research/<slug>/sources/`.
2. **Compile Pedagogical Symbol Table**:
   - After chapters are generated, invoke `source_mapper.py compile-source-map`:
     - Compiles `courses/<slug>/.tc/source-map.toml` with exact line spans for every concept.
     - Compiles `courses/<slug>/.tc/coverage-ledger.md` mathematically proving 100% source chapter coverage.
3. **Encapsulate Course Machine Files in `.tc/`**:
   - Newly created courses must place `course.toml`, `memlog.md`, `consensus-deliberation.md`, `curriculum-brainstorm.md`, `source-map.toml`, `coverage-ledger.md`, and `plans/` inside `courses/<slug>/.tc/`.
   - Root of `courses/<slug>/` has ONLY:
     - `overview.md` (syllabus)
     - `notes/` (compiled textbook chapters)

---

### 5.7 Eliminate Triple Codebase Drift
1. Create `scripts/sync_runtime.py` in the repository root:
   - Automatically synchronizes all scripts from canonical `_tc/scripts/*.py` to:
     - `skills/tc-init/scripts/runtime/*.py`
     - `skills/tc-*/scripts/*.py`
   - Verifies SHA-256 hashes across all copies.
2. In git, ensure NO symlinks or NTFS junctions ever point from `skills/` to `.agents/skills/`.

---

## 6. Step-by-Step Implementation Instructions for Downstream Model

Execute these 5 phases sequentially. Verify after each phase.

### Phase 1: Clean Up Duplicate Directory Generation
1. In `_tc/scripts/bootstrapper.py` and `skills/tc-init/scripts/bootstrapper.py`:
   - Replace `dirs_to_create` list with clean paths: `_tc/scripts`, `profile`, `research`, `courses`, `portfolio`, `roadmap`.
   - Remove references to `.tc`, `plan`, `sources`, `plan/sources`, `_tc/research`.
   - Write config only to `_tc/config.json`.
   - Write preferences only to `profile/preferences.md`.
2. In `_tc/scripts/scout.py` and `skills/tc-research/scripts/scout.py`:
   - Delete lines 824–839 writing to `sources/`, `_tc/research/`, `.tc/research/`.
   - Write exclusively to `research/<slug>/`.
   - Write a single `critique.md` instead of both `five-hats-` and `multi-hats-`.

### Phase 2: Create `paper_fetcher.py` and `book_scout.py`
1. Create `_tc/scripts/paper_fetcher.py` with:
   - `fetch_rfc(rfc_number, target_dir)`
   - `fetch_arxiv_papers(query, target_dir)`
   - `fetch_man_pages(query, target_dir)`
   - CLI `fetch` subcommand emitting structured JSON.
2. Create `_tc/scripts/book_scout.py` with:
   - `search_books(topic)` (Google Books & OpenLibrary)
   - `detect_open_repos(topic)` (GitHub canonical repos)
   - CLI `discover` subcommand emitting structured JSON.
3. Write test cases in `tests/test_paper_fetcher.py` and `tests/test_book_scout.py`.

### Phase 3: Wire Research & Gate 1 into `tc.py`
1. In `_tc/scripts/scout.py`:
   - In `execute_scout()`, call `book_scout.py` and `paper_fetcher.py` to auto-harvest sources into `research/<slug>/sources/` when `--topic` is passed.
   - Aggregate harvested text into `extracted_content`.
   - Write `research/<slug>/gold-standards.md` with explicit statuses.
2. In `_tc/scripts/checkpoint_manager.py`:
   - Update `create_acquisition_gate` to list real books from `book_scout.py` and all auto-downloaded RFCs/papers.
   - Present the 2-option choice (`[1] Proceed with open specs`, `[2] Wait for drop-in`).
3. In `_tc/scripts/tc.py`:
   - Ensure `/tc` calls `scout.py` first and presents Gate 1 before invoking `course_builder.py`.

### Phase 4: Enforce Deterministic Compiler & Encapsulation
1. In `_tc/scripts/course_builder.py`:
   - Remove hardcoded `generate_fact_checking_queries`.
   - Ensure `source_mapper.py` runs during course creation to emit `source-map.toml` and `coverage-ledger.md`.
   - Place all engine files (`course.toml`, `source-map.toml`, `coverage-ledger.md`, `plans/`) inside `courses/<slug>/.tc/`.
   - Root of course has ONLY `overview.md` and `notes/`.

### Phase 5: Codebase Sync & Test Suite Verification
1. Create `scripts/sync_runtime.py` and execute:
   ```bash
   python scripts/sync_runtime.py
   ```
2. Run full pytest suite:
   ```bash
   python -m pytest tests
   ```
   Verify 100% of tests pass with zero regressions.

---

## 7. Acceptance Verification Checklist

| Test Item | Verification Command | Expected Result |
| :--- | :--- | :--- |
| **Clean Git Tree** | `git status` | `nothing to commit, working tree clean` |
| **No 4x Duplicates** | `Get-ChildItem -Path research, sources, _tc -Recurse` | Research files exist ONLY in `research/<slug>/` |
| **Auto-Fetch RFCs** | `python _tc/scripts/paper_fetcher.py fetch --slug test --topic "TLS 1.3"` | Downloads RFC 8446 text directly into `research/test/sources/rfcs/rfc8446.txt` |
| **Canonical Books** | `python _tc/scripts/book_scout.py discover --slug test --topic "Operating Systems"` | Discovers *Modern Operating Systems* (Tanenbaum) and *OSTEP* with ISBN and authors |
| **Material Gate Pause** | `python _tc/scripts/tc.py status` | Pauses at `acquisition_gate` displaying discovered books and auto-fetched specs |
| **Zero RAG / Clean Canvas** | `python -m pytest tests/test_clean_workspace.py` | Course root has ONLY `overview.md`, `notes/`, `.tc/` |
| **Full Regression Suite** | `python -m pytest tests` | All 321+ tests pass |
