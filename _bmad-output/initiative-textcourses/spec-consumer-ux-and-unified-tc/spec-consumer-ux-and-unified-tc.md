---
id: SPEC-consumer-ux-and-unified-tc
companions:
  - interaction-flowchart.md
  - workspace-hierarchy.md
sources:
  - ../brainstorm-rag-utility-and-architecture/brainstorm-rag-utility-and-architecture.md
  - ../spec-multi-source-compiler/spec-multi-source-compiler.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability.

# Consumer UX & Unified `/tc` Interactive Experience

## Why

While the Multi-Source Deterministic Compiler established an industrial-grade backend (verbatim pure-Python extraction, macro TOC deduplication, $O(1)$ symbol tables, and zero-unearned-jargon gates), the user-facing interface remains an "engineer's cathedral": learners are confronted with ten separate slash commands, manual terminal script execution for PDF extraction, exposed agent debate traces that burn unnecessary tokens, and noisy workspaces cluttered with internal machine state files. 

TextCourses transforms this technical substrate into a serene, consumer-grade personal tutor:
1. Collapsing the public surface down to a single, intuitive slash command: `/tc`.
2. Preserving step-by-step interactive human checkpoints (including graceful book-acquisition pauses) rather than unattended steamrolling.
3. Providing zero-terminal drop-in auto-ingestion for PDFs and EPUBs.
4. Encapsulating machine state into a hidden `.tc/` directory to keep the workspace calm and focused.
5. Capping background agent deliberation summaries to strictly under 40 words to prevent token bloat.
6. Preserving the 4-Option Action Fork as the fast-decision control bar at every teaching turn.

## Capabilities

- **CAP-1**
  - **intent:** System consolidates all user-facing interactions behind a single conversational `/tc` entrypoint that intelligently routes intent across onboarding, course creation, and lesson delivery without exposing multiple administrative commands.
  - **success:** In an uninitialized workspace, `/tc` launches interactive setup; when given a topic or books, `/tc` drives the curriculum pipeline; on an active course, `/tc` seamlessly advances or resumes the active lesson.

- **CAP-2**
  - **intent:** System maintains step-by-step interactive checkpoints after research, material acquisition, and course creation, asking the user for confirmation before proceeding to the next phase.
  - **success:** When gold-standard textbooks cannot be openly harvested, `/tc` pauses at an acquisition gate asking the user to supply the file or proceed with open docs; after course synthesis, `/tc` presents the roadmap and awaits user approval before launching Lesson 1.

- **CAP-3**
  - **intent:** System automatically detects any `.pdf` or `.epub` files placed anywhere in the workspace (root, `books/`, `sources/`, `research/`) and invokes verbatim extraction, pre-flight density probing, and symbol table mapping without requiring manual CLI commands.
  - **success:** A user drops textbook files into the workspace and invokes `/tc`; the system discovers, probes, and compiles them automatically, providing empathetic guidance if non-searchable image scans are encountered.

- **CAP-4**
  - **intent:** System encapsulates all internal machine files (`source-map.toml`, `coverage-ledger.md`, `course.toml`, `memlog.md`, `session.jsonl`) inside a hidden `courses/<slug>/.tc/` directory, surfacing only clean human-facing study files (`overview.md` and `notes/`) in the course root.
  - **success:** The user's course folder displays only `overview.md` and compiled textbook notes, while all runtime engines, validators, and audit ledgers operate with zero degradation against the encapsulated `.tc/` directory.

- **CAP-5**
  - **intent:** System executes multi-agent Triad deliberation (Daedalus, Marie, Hypatia) silently in the background and summarizes the reconciliation, deduplication, and coverage audit in a single concise paragraph of 40 words or fewer.
  - **success:** Course synthesis output reports the Triad's consensus, topic deduplication, and 100% coverage verification in $\le 40$ words without burning conversational context on raw multi-turn debate transcripts, while full traces remain inspectable in `.tc/consensus-deliberation.md`.

- **CAP-6**
  - **intent:** System preserves the standardized 4-Option Action Fork at the conclusion of every instructional turn, allowing fast single-digit or natural language decisions while supporting rich conversational follow-up questions.
  - **success:** Every teaching turn concludes with `[1] Next Concept`, `[2] Test Me`, `[3] Re-explain / Deeper`, and `[4] Custom`, responding instantly to numeric inputs (`1`, `2`) as well as organic Socratic inquiries.

## Constraints

- **Potato-Proof Sovereign Execution**: Pure standard Python and local filesystem files; strictly zero GPU requirements, zero vector database dependencies, and zero remote embedding API costs.
- **Token Conservation**: Background agent deliberation summaries displayed in chat must never exceed 40 words.
- **Zero Breaking Changes**: All 296 unit/integration tests must continue passing; backwards compatibility maintained across legacy paths and commands.
- **Strict Zero-BMad Invariant**: Zero mentions of "bmad" anywhere across runtime code, scripts, and user-facing skill files.

## Non-goals

- Discarding internal modular scripts in `_tc/scripts/` (the plumbing remains highly modular and testable; only the user surface is unified).
- Replacing the 4-Option Action Fork with free-form open-ended prompts (the fork remains the primary fast-decision anchor).
- Automatic OCR reconstruction of degraded non-searchable image scans.

## Success signal

A learner drops two textbook PDFs into an empty workspace and types `/tc "Distributed Systems"`. TextCourses detects the books, runs pre-flight density checks, mines community consensus, pauses to confirm the materials, compiles a deduplicated curriculum with 100% coverage parity, outputs a 30-word Triad deliberation summary, and immediately delivers Lesson 1, Turn 1 with the 4-Option Action Fork—all through one command, with zero terminal commands and a clean, clutter-free course folder.

## Assumptions

- Modern AI chat harnesses provide a cleaner, lower-friction user experience when presented with a single authoritative command (`/tc`) rather than a multi-command menu.
- Learners prefer crisp, bounded summaries in chat while retaining the ability to inspect detailed deliberation traces in background files.
