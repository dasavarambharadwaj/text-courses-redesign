# Epic 9: Unified Dispatcher CLI, Session State Continuity & Cross-Platform Integrity

**Initiative**: `initiative-textcourses`  
**Slug**: `epic-unified-dispatcher-session-continuity-and-resilience`  
**Status**: completed  
**Covers**: FR-38, FR-39, FR-40, FR-41  

## Executive Summary
This epic addresses critical architectural, persistence, and reliability findings from the advanced elicitation session:
1. **Unified Runtime Dispatcher (`FR-38`)**: Consolidates all 18 runtime scripts behind a single top-level CLI dispatcher `_tc/scripts/tc.py`. Eliminates triplicate script redundancy across `skills/*/scripts/runtime/` and establishes a single maintainable source of truth.
2. **Persistent Socratic Session State (`FR-39`)**: Upgrades conversational teaching memory by recording structured turn-by-turn dialogue events in `courses/<slug>/session.jsonl`. Guarantees seamless, long-term pedagogical continuity when resuming interrupted lessons across days or weeks.
3. **Dynamic Context-Adaptive Next-Action Fork (`FR-40`)**: Evolves the static Next-Action Fork into a context-aware menu that dynamically adapts its options based on the active pedagogical state (e.g. submitting pending practical labs or advancing completed sections).
4. **Resilient Cross-Platform Hash Checksum Normalization (`FR-41`)**: Normalizes line endings (`\r\n` to `\n`) and strips trailing whitespace before computing SHA-256 integrity checksums in `hash_tracker.py`, preventing false-positive tamper warnings across operating systems and git checkouts.

## Stories Breakdown
1. `story-unified-runtime-dispatcher-plan.md` (FR-38)
2. `story-persistent-socratic-session-state-plan.md` (FR-39)
3. `story-dynamic-adaptive-next-action-fork-plan.md` (FR-40)
4. `story-resilient-cross-platform-hash-normalization-plan.md` (FR-41)
