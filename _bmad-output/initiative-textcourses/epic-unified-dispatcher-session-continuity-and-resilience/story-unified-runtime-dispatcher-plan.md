# Story 1: Unified Runtime Dispatcher CLI (`tc.py`)

**Status**: completed  
**Covers**: FR-38  
**Prerequisites**: None  

## Context & Objectives
Consolidate invocation of the 18 runtime scripts behind a single top-level CLI `_tc/scripts/tc.py`. Provide subcommands:
- `init`: invokes `bootstrapper.py`
- `research`: invokes `scout.py`
- `create`: invokes `course_builder.py`
- `teach`: invokes `teach_engine.py`
- `practicals`: invokes `practical_evaluator.py`
- `test`: invokes `diagnostic_tester.py`
- `notes`: invokes `notes_compiler.py`
- `audit`: invokes `auditor.py`
- `dag`: invokes `dag.py`
- `redirect`: invokes `redirector.py`
- `migrate`: invokes `migrator.py`

## Implementation Steps
1. Create `_tc/scripts/tc.py` with `argparse` subparsers for each core runtime module.
2. Delegate execution cleanly by importing functions or dispatching to module entry points with standard exit codes and `--json` support.
3. Update skills in `skills/` to document the unified `_tc/scripts/tc.py` command as the canonical invocation method.
4. Verify with comprehensive unit tests in `tests/test_tc_dispatcher.py`.
