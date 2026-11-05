# Workspace Hierarchy: Two-Tier Clean Architecture

> **Companion to**: `spec-consumer-ux-and-unified-tc.md`  
> **Purpose**: Specify the file separation between clean human study materials and encapsulated machine state.

---

## 1. The Problem: Workspace Noise & Cognitive Overload

Previously, a generated course dumped 10 machine files directly into the root of `courses/<slug>/`:
- `course.toml`
- `overview.md`
- `consensus-deliberation.md`
- `curriculum-brainstorm.md`
- `memlog.md`
- `session.jsonl`
- `source-map.toml`
- `coverage-ledger.md`
- `notes/chapter-01.md`
- `chapter-01/sec-01/lesson-plan.md`

This made the student's study directory look like an engine room database dump rather than a focused, serene learning environment.

---

## 2. The Two-Tier Clean Hierarchy

All machine substrate files are encapsulated into a hidden `.tc/` subfolder inside the course directory. The user only sees human-facing study files:

```text
workspace/
├── profile/
│   └── preferences.md             <-- The only setting file the user ever edits
│
├── courses/
│   └── distributed-storage/
│       │
│       │── [HUMAN CANVAS: Visible Study Materials]
│       ├── overview.md            <-- High-level curriculum syllabus and progress
│       └── notes/                 <-- Student's compiled textbook notes
│           ├── chapter-01.md
│           └── chapter-02.md
│
│       └── [ENGINE SUBSTRATE: Encapsulated in .tc/]
│           └── .tc/
│               ├── course.toml             <-- Machine DAG manifest
│               ├── source-map.toml         <-- O(1) compile-time symbol table
│               ├── coverage-ledger.md      <-- Zero-omission mathematical audit ledger
│               ├── memlog.md               <-- Dense pedagogical milestone memory
│               ├── session.jsonl           <-- Complete conversational turn history
│               ├── consensus-deliberation.md<-- Full background Triad debate trace
│               ├── curriculum-brainstorm.md<-- Multi-paradigm brainstorm matrix
│               └── plans/                  <-- AI teacher checklist lesson-plans
│                   └── chapter-01/
│                       └── sec-01/
│                           └── lesson-plan.md
```

---

## 3. Backwards Compatibility & Engine Search Path

To guarantee 100% backwards compatibility with existing courses and tests:

Every runtime engine script (`teach_engine.py`, `course_builder.py`, `auditor.py`, `source_mapper.py`, `manifest.py`):
1. **First checks**: `courses/<slug>/.tc/<filename>`
2. **Falls back to**: `courses/<slug>/<filename>`

New courses scaffolded by `course_builder.py` write machine artifacts into `courses/<slug>/.tc/`, while preserving `overview.md` and `notes/` at the root. All existing unit tests pass without modification.
