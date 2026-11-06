---
title: "Mandatory Section-Close Gate, Visible Notes Compilation & Ephemeral Session Scrub"
ticket: 14
status: done
---

# Implementation Plan & Execution: Story 12.14 (CAP-6, CAP-9, FR-11, FR-49)

## Overview
Implement the Mandatory Section-Close Gate across both interactive and auto modes upon mastering the final concept, compiling flat textbook notes under `courses/<slug>/notes/chapter-XX.md`, logging milestones across course and profile scoped memlogs, and permanently scrubbing the ephemeral session transcript (`session.jsonl`).

## Key Changes Made
1. **Section-Close Checkpoint Gate (`_tc/scripts/checkpoint_manager.py`)**:
   - Defined `GATE_SECTION_CLOSE = "section_close"`.
   - Implemented `create_section_close_gate` presenting the visible chapter notes path, section mastery recap, source coverage summary, and 4 actionable options:
     - `[1]` **Approve & Close Section**
     - `[2]` **Revise Notes**
     - `[3]` **Re-explain / Deepen**
     - `[4]` **Keep Session Open**
   - Implemented `approve_section_close` to transition section status to `completed` in `course.toml` across canonical `_tc/` and `.tc/` locations, append scoped memlog milestones (`_tc/courses/<slug>/memlog.md` and profile memlog), permanently scrub/unlink ephemeral `session.jsonl` files, and verify the existence of visible chapter notes.
   - Updated `handle_gate_response` to process section close gate actions.

2. **Teaching Engine Integration (`_tc/scripts/teach_engine.py`)**:
   - In `advance_lesson_concept`, upon completing the final concept in a section, automatically compile visible notes via `compile_notes` and immediately open the Mandatory Section-Close Gate.
   - Halts progression until the close gate is approved.

3. **Visible Chapter Notes Target Path (`_tc/scripts/notes_compiler.py`)**:
   - Fixed `visible_course_dir` resolution so that `notes/chapter-XX.md` is strictly written to the learner-facing `courses/<slug>/notes/chapter-XX.md` directory regardless of whether the manifest was discovered in `.tc/` or `_tc/`.

4. **Dispatcher Continuation (`_tc/scripts/tc.py`)**:
   - Updated `dispatch_conversational_turn` to handle `action == "approve_close"` from the pending section close gate and transition state to `section_closed`.

5. **Verification**:
   - Created comprehensive test suite in `tests/test_section_close_gate.py` (4 tests passing).
   - Zero regressions across `tests/test_interactive_gates.py`, `tests/test_adaptive_fork.py`, `tests/test_beginner_adaptation.py`, and `tests/test_runtime_engine_integration.py`.
