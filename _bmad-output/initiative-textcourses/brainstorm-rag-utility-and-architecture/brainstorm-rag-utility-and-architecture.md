# Intent: Multi-Source Deterministic Compiler (Replacing Runtime RAG)

> **Document Type**: BMad Brainstorm Intent Document  
> **Source Session**: `_bmad-output/initiative-textcourses/brainstorm-rag-utility-and-architecture/.memlog.md`  
> **Status**: Settled / Ready for PRD & Architecture Specification  
> **Date**: 2026-11-02  
> **Downstream Skills**: `bmad-prd`, `bmad-architecture`, `bmad-spec`

---

## 1. Problem Statement & Paradigm Shift

### The Flaw of Traditional RAG in Structured Education
Standard RAG pipelines (chunking texts into 500-token fragments, embedding into vectors, and performing runtime similarity search) fail in structured learning:
1. **Probabilistic Retrieval Misses**: 10–20% of queries retrieve irrelevant or partial paragraphs.
2. **Context Fragmentation**: Arbitrary token boundaries slice mathematical formulas, code blocks, and multi-paragraph proofs in half.
3. **Broken Pedagogical Sequence**: Runtime searches pull advanced concepts before foundational axioms have been introduced.
4. **Vocabulary Mismatch**: Lexical BM25 or naive vector similarity fails when a learner uses a synonym not verbatim in the source.

### The Solution: We Are Removing Traditional RAG
TextCourses discards runtime probabilistic RAG for core curriculum delivery. In its place, TextCourses introduces the **Multi-Source Deterministic Compiler**:
- Course creation functions as a **Pedagogical Compiler**.
- It ingests source books verbatim, deduplicates overlapping topics across multiple peer sources, and pre-computes an exact **Pedagogical Symbol Table (`source-map.toml`)**.
- At teaching time, retrieval is a deterministic **$O(1)$ pointer lookup** into the exact verified text.

---

## 2. Core Value Proposition: Multi-Source Peer Synthesis

The primary differentiator of TextCourses is **multi-source cross-synthesis without loss of context**:
- Learners provide multiple heterogeneous materials (e.g. 2 textbooks, 3 research papers, official documentation).
- There is **no primary anchor hierarchy**; all sources stand as first-class peers.
- **Deduplication**: Identical topics (e.g. LSM-Trees, 2-Phase Commit, Quorum protocols) are synthesized and taught **exactly once**.
- **Dialectic Merging**: When sources teach differing approaches, architectures, or trade-offs, TextCourses merges them into a single comparative lesson highlighting both viewpoints.

---

## 3. System Architecture & Pipeline

```
[PDFs, EPUBs, Repos, MDs]
           │
           ▼
[Pass 0: Raw Ingestion]
  - Pure Python verbatim extraction (pypdf / pdfplumber)
  - Zero LLM rewriting / 100% code and symbol fidelity
  - Pre-flight text density probe (fail-fast on non-searchable scanned image PDFs)
           │
           ▼
[Pass 1: Macro TOC Alignment]
  - Extract Table of Contents ASTs (toc.json) without LLM token bloat
  - Semantic clustering of overlapping topics across books
  - Build unified master topological DAG (acyclic prerequisite ordering)
           │
           ▼
[Pass 2: Conveyor-Belt Ingestion Pipeline]
  - Chapter-by-chapter sequential processing (prevents 600-page context window rot)
  - Accumulates running vocabulary ledger between chapters
  - Generates:
      1. source-map.toml (concept-to-exact-source-line-spans)
      2. coverage-ledger.md (mathematical audit proving 100% of book chapters covered)
           │
           ▼
[Pass 3: The Grounded Sensei Delivery]
  - O(1) pointer lookup loads exact pre-mapped source text into teach_engine
  - Separation of Powers: Book provides the Floor (invariants); Sensei provides the Lift
  - Strict Vocabulary Contract: Zero unearned jargon
```

---

## 4. The Pedagogical Law: Grounded Sensei Voice & Vocabulary Contract

1. **Tone Decoupling**: Academic pedantry, dense tone, or dry jargon in source books must never dictate the teaching tone. The teacher always uses clear, human-accessible language aligned with learner preferences (Feynman, Hypatia, Turing, or hybrid blend).
2. **The Vocabulary Contract (Zero Unearned Jargon)**:
   - A technical term can never be used unless:
     - It was introduced and logged in a previous turn/lesson, OR
     - It is the designated new term being introduced this turn.
   - **Intuition-Before-Label**: The physical, real-world reality must always be explained in plain English *before* affixing the formal technical label.
3. **Multi-Source Demystification**: When sources use conflicting terminology (e.g. "Leader" vs "Primary"), the Sensei teaches the core concept in plain English and notes the industry synonym as a brief clarifying aside.

---

## 5. MoSCoW Feature Matrix for Implementation

| Priority | Feature Component | Functional Requirement |
| :--- | :--- | :--- |
| **MUST** | `extractor.py` | Pure Python verbatim PDF/text extraction to raw markdown with zero LLM rewriting. |
| **MUST** | `source-map.toml` | Compile-time mapping of every concept in `lesson-plan.md` to exact source files, heading paths, and line spans. |
| **MUST** | Multi-Source Deduplication | Pass 1 algorithm clustering shared topics across multiple sources into a single DAG node. |
| **MUST** | Conveyor-Belt Pipeline | Sequential chapter-bounded digestion loop preventing context rot on 500+ page books. |
| **MUST** | Vocabulary Contract | Verification gate in `teach_engine.py` ensuring zero unearned jargon appears in lesson turns. |
| **SHOULD** | `coverage-ledger.md` | Audit tool verifying 100% of chapters/sections in source books are mapped into the curriculum. |
| **SHOULD** | Pre-Flight Scanned PDF Probe | Automatic character density check warning users if a PDF lacks a digital text layer. |
| **SHOULD** | Auxiliary BM25 Search | Keep local SQLite FTS5 index solely for handling unexpected off-syllabus learner inquiries (`[4] Custom`). |
| **WON'T** | Heavy Vector DBs | Zero ChromaDB, Pinecone, or GPU embedding models (maintaining potato-proof 0MB overhead). |
| **WON'T** | Runtime Vector Chunks | Complete removal of runtime chunk searching for syllabus teaching. |
