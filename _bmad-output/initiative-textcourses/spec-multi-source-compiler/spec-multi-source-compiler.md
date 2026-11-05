---
id: SPEC-multi-source-compiler
companions:
  - architecture-diagrams.md
  - source-map-schema.md
  - vocabulary-contract.md
sources:
  - ../brainstorm-rag-utility-and-architecture/brainstorm-rag-utility-and-architecture.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Multi-Source Deterministic Compiler

## Why

Runtime probabilistic RAG (fuzzy vector search across 500-token chunks) fundamentally fails structured education by slicing formulas and code in half, dropping 10–20% of relevant passages through vocabulary mismatch, and losing prerequisite sequence. Learners who study from multiple authoritative textbooks and research papers are forced to endure repetitive overlapping introductions and reconcile competing terminologies themselves. TextCourses eliminates runtime RAG for core lessons and introduces the Multi-Source Deterministic Compiler: an autonomous pedagogical compiler that ingests heterogeneous peer books verbatim, deduplicates overlapping primitives into a single acyclic syllabus, pre-computes an exact $O(1)$ symbol table (`source-map.toml`), and delivers lessons through a Grounded Sensei bound by an ironclad zero-unearned-jargon contract.

## Capabilities

- **CAP-1**
  - **intent:** System extracts raw textual prose, code snippets, tables, and heading structures from user-provided PDFs/EPUBs into verbatim markdown with zero LLM rewriting.
  - **success:** A multi-page PDF containing code blocks and formulas yields exact markdown without loss of mathematical notation, variable names, or indentation, while scanned non-searchable image PDFs trigger a pre-flight warning without crashing.

- **CAP-2**
  - **intent:** System extracts Table of Contents ASTs across multiple heterogeneous sources and clusters overlapping topics into a single deduplicated topological DAG.
  - **success:** When supplied with multiple books covering overlapping domains, the resulting course syllabus teaches each common primitive exactly once while preserving all source-unique niche topics.

- **CAP-3**
  - **intent:** System processes large multi-hundred-page textbooks sequentially chapter-by-chapter with running vocabulary accumulation to prevent LLM context rot.
  - **success:** Ingestion of a 500+ page textbook completes with peak prompt token usage remaining bounded below 25,000 tokens per step, without omitting any chapter or section.

- **CAP-4**
  - **intent:** System pre-maps every concept in `lesson-plan.md` to exact source files, heading breadcrumbs, and line number spans at course creation time.
  - **success:** `source-map.toml` is generated with 100% of concepts linked to verifiable line ranges, and `teach_engine.py session` loads the exact mapped text via $O(1)$ direct lookup without invoking runtime vector search.

- **CAP-5**
  - **intent:** System generates an audit matrix matching every chapter and section of the uploaded source books to its corresponding course section.
  - **success:** `coverage-ledger.md` is emitted at course creation, mathematically auditing source-to-curriculum parity and failing course validation if any source section was dropped.

- **CAP-6**
  - **intent:** System delivers lessons using the learner's chosen teacher style in simple, jargon-free plain English, strictly forbidding any technical term unless taught in prior turns or introduced this turn with everyday intuition first.
  - **success:** `teach_engine.py` validates that no unintroduced technical jargon appears in instructional turns, and multi-source differences are synthesized as dialectic comparisons rather than competing jargon.

## Constraints

- **Potato-Proof Sovereign Hardware**: Must operate 100% locally with standard library Python and filesystem files; strictly zero GPU requirements, zero vector databases (no ChromaDB, Pinecone, FAISS), and zero external embedding APIs.
- **Pure-Python Ingestion**: PDF extraction must rely on pure-Python libraries (`pypdf` / `pdfplumber`) with zero mandatory external system binary dependencies (`pandoc` / `pdftotext` optional).
- **Bounded Ingestion Context**: Peak prompt tokens during conveyor-belt chapter ingestion must never exceed 25,000 tokens per turn.

## Non-goals

- Automatic OCR reconstruction of degraded non-searchable image scans (user must supply searchable text/pdf).
- Vector embeddings, vector databases, or probabilistic chunk searching for syllabus lesson delivery.
- Rigid adherence to textbook academic tone or pedantry during teaching turns.

## Success signal

A learner drops two 500-page textbooks (*Designing Data-Intensive Applications* and *Database Internals*) and an academic paper (*Raft Consensus*) into `research/<slug>/sources/`; TextCourses compiles them into a single unified course where LSM-Trees and Leader Election are taught exactly once with dialectic trade-offs, 100% of book chapters are verified in `coverage-ledger.md`, and every lesson turn loads the exact source passages in under 5 milliseconds with zero unearned jargon.

## Assumptions

- Modern LLMs at teaching time are sufficiently capable of parsing raw extracted text and line wraps into clean markdown code blocks without requiring complex visual layout reconstruction.
