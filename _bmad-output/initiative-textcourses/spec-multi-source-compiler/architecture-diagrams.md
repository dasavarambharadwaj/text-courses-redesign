# Architecture Diagrams: Multi-Source Deterministic Compiler

> **Companion to**: `spec-multi-source-compiler.md`  
> **Rule**: Diagrams always land in a companion per BMad Spec Law Rule 2.

---

## 1. End-to-End Compiler Pipeline

```mermaid
flowchart TD
    subgraph Inputs["1. Multi-Source Ingestion"]
        B1["Book A (PDF/EPUB)"]
        B2["Book B (PDF/EPUB)"]
        B3["Paper C (Markdown)"]
    end

    subgraph Pass0["Pass 0: Verbatim Extraction"]
        EXT["extractor.py (pypdf / pdfplumber)"]
        RAW["Raw Markdown Files (Zero LLM Rewriting)"]
    end

    subgraph Pass1["Pass 1: Macro TOC Alignment"]
        TOC["TOC Parser (toc.json trees)"]
        DAG["Topological Deduplication Engine"]
        MDAG["Unified Master Curriculum DAG"]
    end

    subgraph Pass2["Pass 2: Conveyor-Belt Ingestion"]
        CB["Chapter-by-Chapter Sequential Ingestion"]
        VOC["Running Vocabulary & Axiom Ledger"]
        SMAP["source-map.toml (Symbol Table)"]
        CLED["coverage-ledger.md (Audit Matrix)"]
    end

    subgraph Pass3["Pass 3: Grounded Sensei Delivery"]
        TE["teach_engine.py session"]
        GS["Grounded Sensei (Feynman / Hypatia / Turing)"]
        STU["Learner Turn (Zero Unearned Jargon)"]
    end

    B1 & B2 & B3 --> EXT
    EXT --> RAW
    RAW --> TOC
    TOC --> DAG
    DAG --> MDAG
    MDAG --> CB
    CB <--> VOC
    CB --> SMAP & CLED
    SMAP --> TE
    TE --> GS
    GS --> STU
```

---

## 2. Multi-Source Deduplication & Dialectic Synthesis

```mermaid
flowchart LR
    subgraph Sources["Heterogeneous Peer Sources"]
        DDIA["Kleppmann (DDIA): §3.2 SSTables & LSM-Trees"]
        DBI["Petrov (DB Internals): §5.4 LSM-Tree Compaction"]
    end

    subgraph Compiler["Deduplication & Dialectic Engine"]
        ALIGN["Identify Semantic Intersection: LSM-Trees"]
        MERGE["Synthesize Complementary Angles:<br/>Write Throughput vs Read Amplification"]
    end

    subgraph Output["Unified Curriculum Output"]
        MAP["source-map.toml Entry:<br/>• Sources: [DDIA §3.2, DBI §5.4]<br/>• Dialectic: true"]
        LESSON["Grounded Sensei Lesson:<br/>Taught ONCE with both viewpoints synthesized"]
    end

    DDIA & DBI --> ALIGN
    ALIGN --> MERGE
    MERGE --> MAP
    MAP --> LESSON
```

---

## 3. Conveyor-Belt Context Management (Preventing Context Rot)

```mermaid
sequenceDiagram
    participant Orch as Course Builder Orchestrator
    participant LLM as LLM Ingestion Context
    participant Led as Running Vocabulary Ledger
    participant SMap as source-map.toml

    Note over Orch,LLM: Ingesting 600-Page Textbook (< 25k tokens/turn)
    
    Orch->>LLM: Ingest Chapter 1 Text (~8,000 tokens)
    LLM-->>Orch: Chapter 1 Lesson Plan + Line Spans
    Orch->>Led: Append Initial Axioms: [SLA, Latency, Storage]
    Orch->>SMap: Write Chapter 1 Source Pointers

    Orch->>LLM: Ingest Chapter 2 Text + Running Axioms (~12,000 tokens)
    LLM-->>Orch: Chapter 2 Lesson Plan + Line Spans
    Orch->>Led: Append New Axioms: [SSTable, Compaction]
    Orch->>SMap: Write Chapter 2 Source Pointers

    Note over Orch,LLM: Repeats sequentially for all chapters with zero context rot
```
