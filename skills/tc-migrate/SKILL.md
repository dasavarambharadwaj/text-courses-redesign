---
name: tc-migrate
description: "Audit workspace schema health and execute consent-gated directory and configuration migrations."
---

# `tc-migrate`: Consent-Gated Schema Migrator & Health Auditor

`tc-migrate` ensures sovereign TextCourses workspaces remain healthy and up to date as schema layouts and runtime engines evolve.

## Core Invariants

1. **Strict Consent Gate (AD-8)**: Never mutate or move files on disk without explicit typed confirmation (`--confirm APPLY`).
2. **Transparent Dry-Run Plan**: Always generate a clear `migration-plan.md` report showing planned operations before any execution.
3. **Preservation of Learner Artifacts**: Never delete or rewrite completed learner notes, assessments, or portfolio artifacts during migration.
4. **Deterministic Auditing (FR-21)**: Validate required directory structures, configuration versions, and runtime scripts deterministically.

---

## Workflow

### 1. Workspace Health Audit

Run health check across the workspace:

```bash
uv run _tc/scripts/migrator.py check --path .
```

The script reports:
- `status`: `"healthy"`, `"needs_migration"`, or `"corrupt"`.
- `current_version`: Schema version detected in `.tc/config.json`.
- `target_version`: Engine target schema version (e.g. `0.2.0`).
- `missing_directories`: Directories required by TextCourses.
- `missing_scripts`: Any runtime scripts missing from `_tc/scripts/`.

If the workspace is already healthy, no migration is required.

### 2. Generate Dry-Run Migration Plan

If the workspace `needs_migration`, generate a dry-run migration plan:

```bash
uv run _tc/scripts/migrator.py plan --path .
```

This outputs planned operations to stdout and writes `migration-plan.md` to the workspace root. Review this report with the learner.

### 3. Solicit Explicit Typed Consent

Explain the planned actions to the learner. Present the migration plan clearly and explain what will be updated (e.g. adding missing directories, updating config version, synchronizing runtime scripts).

**Do not proceed without explicit user confirmation.**

### 4. Execute Migration

Once confirmed by the learner, apply the migration:

```bash
uv run _tc/scripts/migrator.py apply --path . --confirm APPLY
```

The script executes the migration atomically, removes the temporary `migration-plan.md`, and returns exit code 0.
