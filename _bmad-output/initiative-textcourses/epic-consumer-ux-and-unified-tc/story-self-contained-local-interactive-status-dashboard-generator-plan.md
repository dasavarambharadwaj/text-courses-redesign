---
title: "Self-Contained Local Interactive Status Dashboard Generator"
ticket: 15
status: done
---

# Implementation Plan & Execution: Story 12.15 (CAP-10, FR-50)

## Overview
Implement the static status dashboard generator writing `status-board/index.html` from `_tc/status/state.json` upon initialization and every state mutation. Opens offline directly via `file://` with zero external network requests.

## Key Changes Made
1. **State Collector & Dashboard Generator (`_tc/scripts/dashboard_generator.py`)**:
   - `collect_workspace_state`: Gathers structured state tree reading canonical `_tc/` files (`config.json`, `preferences.md`, active checkpoint gate, courses, research substrates, conversion ledger, 4-hat debate, and scoped memlog timeline).
   - Writes compiled state to `_tc/status/state.json`.
   - `generate_dashboard_html`: Emits a modern, responsive, 100% self-contained single-file HTML document to `status-board/index.html`.
     - Zero external network requests: no external CDN links, web fonts, or remote scripts. Standalone CSS, inline SVGs, and embedded vanilla JavaScript.
     - Features:
       - Active Checkpoint Gate callout banner with prompt and available options.
       - Next Action / Focus card.
       - Quick metrics (Active courses, sections completed, overall mastery, indexed sources).
       - Visual Curriculum & Roadmap DAG with progress bars and status badges.
       - Multi-Source Research Substrate overview with conversion coverage proof and debate summary.
       - Searchable and filterable Memlog & Decision feed.
   - `write_status_dashboard`: Atomic helper writing both `_tc/status/state.json` and `status-board/index.html`.

2. **Integration into Workspace Lifecycle**:
   - Integrated into `bootstrapper.py` so fresh workspace bootstrapping immediately generates the status board and initial state.
   - Integrated into `tc.py` so every turn dispatch, mode update, course creation, and checkpoint response regenerates the status board.

3. **Runtime Synchronization & Tests**:
   - Synced scripts across runtime and skills directories.
   - Verified with unit tests in `tests/test_status_dashboard.py` (5 tests passing).
   - Zero regressions across `tests/test_bootstrapper.py` and `tests/test_storage_contract.py`.
