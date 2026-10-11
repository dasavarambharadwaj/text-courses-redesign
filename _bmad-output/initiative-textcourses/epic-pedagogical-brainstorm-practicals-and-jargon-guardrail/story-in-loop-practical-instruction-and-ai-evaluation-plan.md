# Story Plan: In-Loop Practical Instruction & AI Practical Evaluation

**Story ID**: 3  
**Epic**: `epic-pedagogical-brainstorm-practicals-and-jargon-guardrail`  
**Status**: in-progress  
**Covers**: FR-36  

## Context & Objectives
When a learner indicates they want to learn with practicals (`practical_focus = true`, hands-on exercises, or labs):
1. **Teaching Loop Integration**: `/tc-teach` incorporates Daedalus (The Master Craftsman) directly into the teaching cycle for every lesson.
2. **Lesson Challenge Scaffolding**: Every lesson generates a concrete hands-on lab in `courses/<slug>/lessons/lesson-XX/practical.md` containing:
   - Challenge brief & system invariants
   - Starter code / baseline skeleton
   - Verification test criteria / edge cases to handle
3. **AI Evaluation Loop**: When the learner submits code, `practical_evaluator.py` evaluates the submission via AI rubric:
   - Correctness against required invariants
   - Boundary & edge-case resiliency
   - Idiomatic craft & clean structure
   - Actionable diagnostic guidance on failure
4. **Mastery Gate**: Practical verification is logged in `ledger.toml` and gates section progression.

## Acceptance Criteria
1. `teach_engine.py` generates `practical.md` for lessons when practical focus is active.
2. `practical_evaluator.py` provides `evaluate_submission()` with structured scoring and actionable diagnostic feedback.
3. `/tc-teach` and `/tc-practicals` coordinate seamlessly to evaluate student work.
4. Unit tests verify practical generation, AI evaluation parsing, and ledger progression gating.
