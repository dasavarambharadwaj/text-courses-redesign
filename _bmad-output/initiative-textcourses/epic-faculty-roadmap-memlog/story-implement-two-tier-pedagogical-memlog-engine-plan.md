---
title: "Implement Two-Tier Pedagogical Memlog Engine (memlog.py)"
type: "feature"
ticket: 1
created: "2026-10-11"
status: done
route: "full"
route_source: "auto"
risk: "low"
review: "quick"
review_source: "pinned"
lenses_ran: ["quick-lens"]
review_loop_iteration: 1
context:
  - "_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md"
  - "_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md"
  - "_bmad-output/initiative-textcourses/epic-faculty-roadmap-memlog/epic-faculty-roadmap-memlog.md"
---

# Story Plan: Implement Two-Tier Pedagogical Memlog Engine (`memlog.py`)

## 1. Context & Scope
This story implements the deterministic runtime substrate for **FR-28 (Two-Tier Pedagogical Memory Logging)**. 
It deploys `_tc/scripts/memlog.py` conforming to PEP 723 standards, providing:
- POSIX-compliant atomic file writes using `O_APPEND` / temp file replacements.
- Structured pedagogical tagging: `concept`, `question`, `insight`, `misconception`, `analogy`, `handoff`, `milestone`, `decision`.
- Subcommands: `init`, `append`, `set`, `inspect`, `tail` (returning compact trailing $N$ entries for turn context injection).
- Comprehensive unit tests in `tests/test_memlog.py` verifying concurrency, atomicity, and schema compliance.

## 2. Requirements & Invariants
- **PEP 723 Inline Metadata**: Declares Python 3.11+ requirement with zero heavy external dependencies.
- **Append-Only Chronological Integrity**: History is immutable; entries land strictly at EOF in source order.
- **Context Injection**: `tail --n 15` outputs JSON digest ready for `/tc-teach` turn recovery without token bloat.

## 3. Implementation Steps
1. Create `_tc/scripts/memlog.py` with CLI subcommands (`init`, `append`, `set`, `inspect`, `tail`).
2. Implement atomic file writing and OS-level append semantics.
3. Author `tests/test_memlog.py` covering all CLI subcommands, tag formatting, and trailing context extraction.
4. Execute test suite via `uv run pytest tests/test_memlog.py`.
