# Schema Specification: `source-map.toml` & `coverage-ledger.md`

> **Companion to**: `spec-multi-source-compiler.md`  
> **Purpose**: Formal data structures for compile-time deterministic grounding and complete-coverage auditing.

---

## 1. `source-map.toml` (The Pedagogical Symbol Table)

Stored at `courses/<slug>/source-map.toml`. This file maps every concept in the curriculum directly to verifiable line spans in the raw source markdown files.

### TOML Schema

```toml
# courses/<slug>/source-map.toml
version = "1.0.0"
course_slug = "distributed-systems"
compiled_at = "2026-11-02T12:00:00Z"

[[sources]]
id = "ddia"
title = "Designing Data-Intensive Applications"
author = "Martin Kleppmann"
raw_path = "research/distributed-systems/sources/raw/ddia.md"
total_lines = 14250

[[sources]]
id = "db-internals"
title = "Database Internals"
author = "Alex Petrov"
raw_path = "research/distributed-systems/sources/raw/database-internals.md"
total_lines = 11800

[[chapters]]
slug = "chapter-01-storage-engines"
title = "Storage Engines & Compaction"

  [[chapters.sections]]
  slug = "section-02-lsm-trees"
  title = "Log-Structured Merge-Trees and Compaction"

    [[chapters.sections.concepts]]
    id = "lsm-tree-architecture"
    title = "Log-Structured Merge-Tree Architecture"
    dialectic = true
    synthesis_notes = "Kleppmann focuses on write throughput and sequential I/O; Petrov details sparse in-memory index structures and binary search."
    
    [[chapters.sections.concepts.pointers]]
    source_id = "ddia"
    heading = "SSTables and LSM-Trees"
    lines = [412, 485]
    verbatim_anchor = "The storage engine keeps an in-memory balanced tree structure (like a red-black tree), called a memtable."

    [[chapters.sections.concepts.pointers]]
    source_id = "db-internals"
    heading = "LSM Tree Compaction Algorithms"
    lines = [890, 1020]
    verbatim_anchor = "Size-tiered compaction triggers when multiple SSTables of approximately equal size accumulate."
```

### Retrieval Invariant in `teach_engine.py`

When `teach_engine.py session` executes for an active concept:
1. Engine reads `courses/<slug>/source-map.toml`.
2. Locates `chapters.sections.concepts` matching the active concept ID.
3. Performs a direct file read on `raw_path` using the slice `lines[0]:lines[1]`.
4. Delivers the verified verbatim text directly in `rag_source_excerpts`.
5. **Computational Complexity**: $O(1)$ dictionary lookup + single sequential file slice. Zero vector search, zero miss rate.

---

## 2. `coverage-ledger.md` (The Zero-Omission Audit Matrix)

Stored at `courses/<slug>/coverage-ledger.md`. This markdown document mathematically audits that every chapter, section, and subsection in the uploaded source materials has a verified mapping in the curriculum.

### Format & Structure

```markdown
# Coverage Audit Ledger: Distributed Systems

- **Audit Date**: 2026-11-02
- **Course Slug**: distributed-systems
- **Sources Audited**: 2 books, 1 paper
- **Overall Coverage Ratio**: 100.0% (38 / 38 source sections mapped)
- **Status**: PASSED

## Source: Designing Data-Intensive Applications (Martin Kleppmann)

| Source Section | Source Title | Mapped Course Chapter / Section | Status |
| :--- | :--- | :--- | :--- |
| **§1.1** | Reliability: Faults vs Failures | Chapter 1 » Section 1: Foundations | [✓] Mapped |
| **§1.2** | Scalability: Describing Load & Performance | Chapter 1 » Section 2: Measuring Scale | [✓] Mapped |
| **§3.1** | Hash Indexes | Chapter 2 » Section 1: In-Memory Indexing | [✓] Mapped |
| **§3.2** | SSTables and LSM-Trees | Chapter 2 » Section 2: LSM Storage (Dialectic) | [✓] Mapped |
| **§3.3** | B-Trees | Chapter 3 » Section 1: Page-Based B-Trees | [✓] Mapped |

## Source: Database Internals (Alex Petrov)

| Source Section | Source Title | Mapped Course Chapter / Section | Status |
| :--- | :--- | :--- | :--- |
| **§2.1** | Disk-Based Storage Basics | Chapter 1 » Section 1: Foundations (Merged) | [✓] Deduplicated |
| **§4.2** | B-Tree Variants (B+, B*, Bw-Tree) | Chapter 3 » Section 2: Specialized Trees (Niche) | [✓] Mapped (Preserved) |
| **§5.4** | Size-Tiered vs Leveled Compaction | Chapter 2 » Section 2: LSM Storage (Dialectic) | [✓] Mapped |

## Validation Gate
- Total Source Sections Discovered: 38
- Mapped to Canonical Course Nodes: 31
- Deduplicated / Merged as Common Primitives: 7
- Unmapped / Dropped Sections: 0
- **Audit Verdict**: PASSED. Course scaffolding authorized.
```
