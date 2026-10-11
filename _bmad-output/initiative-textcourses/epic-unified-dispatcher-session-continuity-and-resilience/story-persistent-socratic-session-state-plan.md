# Story 2: Persistent Socratic Session State Machine

**Status**: completed  
**Covers**: FR-39  
**Prerequisites**: Story 1 (`tc.py`)  

## Context & Objectives
Upgrade the instruction engine (`teach_engine.py`) to log turn-by-turn interactive snapshots to `courses/<slug>/session.jsonl`.
This allows the conversational teacher persona to restore deep mental context when a student resumes after an interruption.

## Implementation Steps
1. In `_tc/scripts/teach_engine.py`, add `append_session_log(course_dir, entry)` and `load_session_context(course_dir, limit=5)`.
2. Ensure each entry records:
   - `timestamp`: ISO-8601 UTC timestamp.
   - `section_id` & `concept`: Active learning milestone.
   - `teacher`: Active faculty persona.
   - `turn_type`: "concept_delivery", "student_response", "socratic_probe", or "remediation".
   - `summary`: Compact summary of the exchange.
3. Update `get_teaching_session()` to return `recent_session_history` loaded from `session.jsonl`.
4. Add CLI subcommands `log-turn` and `history` to `teach_engine.py`.
5. Verify with unit tests in `tests/test_session_state.py`.
