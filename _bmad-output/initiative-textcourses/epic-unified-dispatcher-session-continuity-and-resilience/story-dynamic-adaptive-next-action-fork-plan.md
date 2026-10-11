# Story 3: Dynamic Context-Adaptive Next-Action Fork

**Status**: completed  
**Covers**: FR-40  
**Prerequisites**: Story 1, Story 2  

## Context & Objectives
Evolve the Next-Action Fork from a static 4-option menu into a context-adaptive dispatch fork that dynamically reflects the student's exact learning situation.

## Implementation Steps
1. In `_tc/scripts/teach_engine.py`, replace static `NEXT_ACTION_FORK_TEXT` with a function `render_next_action_fork(session_state)`.
2. Support distinct states:
   - **In-Concept Progression**:
     - `[1]` Next Concept
     - `[2]` Test Me on Concept
     - `[3]` Re-explain / Deeper Analogy
     - `[4]` Custom Inquiry
   - **Practical Challenge Pending**:
     - `[1]` Submit Practical Solution (Daedalus Evaluator)
     - `[2]` View Practical Lab Instructions & Hints
     - `[3]` Ask Socratic Question on Implementation
     - `[4]` Skip / Defer Practical
   - **Section Concepts Completed (Ready to Lock)**:
     - `[1]` Finalize & Compile Chapter Notes
     - `[2]` Comprehensive Section Diagnostic Challenge
     - `[3]` Review Section Mechanics
     - `[4]` Custom Section Question
3. Expose dynamic fork in `teach_engine.py session` output and Next-Action Fork markdown block.
4. Verify with unit tests in `tests/test_adaptive_fork.py`.
