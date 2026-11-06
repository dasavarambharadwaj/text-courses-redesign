---
title: "Multi-Source Discovery, Interactive Source Proposal & Material Fallback Loop"
ticket: 10
status: done
epic: epic-consumer-ux-and-unified-tc
covers: [CAP-8, FR-43]
completed_at: "2026-11-06T20:41:00+05:30"
---

# Story 12.10: Multi-Source Discovery, Interactive Source Proposal & Material Fallback Loop (CAP-8, FR-43)

## Summary
Implemented the comprehensive multi-source discovery across 6 channels (Canonical Books, Academic Research Papers, Official Standards & RFCs, GitHub Repositories, Community Consensus, and Curated Web Documentation). Generated human-readable and structured source proposals at `_tc/research/<slug>/source-proposal.md` and integrated the 5-option interactive proposal gate (`[1] Approve Sources & Fetch All`, `[2] Request More Research`, `[3] Add Custom Source`, `[4] Remove Source`, `[5] Stop`) with non-stalling scoped memlog fallback logging for proprietary textbooks.

## Architectural Changes & Implementation Details
1. **Multi-Source Discovery across 6 Channels (`_tc/scripts/scout.py`)**:
   - Implemented `generate_source_proposal_markdown(slug, topic, canonical_books, official_sources, ...)` formatting rich proposals across the 6 channels.
   - Updated `run_scout` to write `source-proposal.md` to canonical `_tc/research/<slug>/source-proposal.md` with legacy mirroring.
   - Enhanced `digest.json` and returned scout metadata with `source_proposal_path`.
2. **Interactive Proposal Checkpoint Gate (`_tc/scripts/checkpoint_manager.py`)**:
   - Defined `GATE_SOURCE_PROPOSAL = "source_proposal"`.
   - Implemented `create_source_proposal_gate(workspace, slug, topic, proposal_path, recommended_books, found_sources)`.
   - Expanded `handle_gate_response` to parse:
     - `1` / `approve`: `action: "proceed_open"` (clears gate, advances to fetch-all and blueprint scaffolding).
     - `2` / `more` / `more research`: `action: "more_research"` (keeps gate active, re-runs deep scouting).
     - `3` / `add <source>`: `action: "add_source"` (appends custom source to proposal).
     - `4` / `remove <source>`: `action: "remove_source"` (excludes source from proposal).
     - `5` / `stop`: `action: "stop"` (clears gate, cancels course creation).
3. **Dispatcher & Material Fallback Engine (`_tc/scripts/tc.py`)**:
   - In interactive mode on a new topic, pauses at the source proposal checkpoint gate with `active_artifact: _tc/research/<slug>/source-proposal.md`.
   - On approval (`proceed_open`), executes `harvest_official_sources` (fetch-all) and checks for missing proprietary textbooks:
     - In auto mode: non-silently logs the gap to `_tc/profile/memlog.md` and `_tc/research/<slug>/memlog.md` and continues with open specs and papers.
     - In interactive mode: logs the fallback to `_tc/research/<slug>/memlog.md`.
4. **Harvester & Paper Fetcher Canonicalization (`_tc/scripts/harvester.py`, `_tc/scripts/paper_fetcher.py`)**:
   - Canonicalized write paths to `_tc/research/<slug>/sources/` (repos, transcripts, rfcs, docs, papers) with legacy mirrors.

## Verification
- Created `tests/test_source_approval_loop.py` (5 tests, 100% passed):
  - `test_scout_generates_source_proposal_across_channels`
  - `test_checkpoint_source_proposal_gate_options`
  - `test_dispatch_source_approval_workflow`
  - `test_dispatch_more_research_and_add_source_interaction`
  - `test_material_fallback_logging_in_auto_and_interactive`
- Ran regression suite (`tests/test_interactive_gates.py`, `tests/test_mode_selection.py`, `tests/test_public_surface.py`, `tests/test_dispatcher_continuation.py`, `tests/test_unified_tc.py`): 23 passed in 31.7s.
