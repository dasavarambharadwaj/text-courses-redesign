---
name: tc-redirect-course
description: "Inspect documentation source drift and manage non-destructive course evolution and notes deprecation."
---

# `tc-redirect-course`: Course Evolution & Non-Destructive Deprecation

`tc-redirect-course` enables non-destructive course evolution when ingested reference materials, API documentation, or frameworks drift or update over time.

## Core Invariants

1. **Immutable Learner Notes (AD-7)**: Completed `notes.md` files are permanent, sovereign learner artifacts. Never rewrite, delete, or modify historical notes bodies bit-for-bit.
2. **Prepend-Only Deprecation**: If material is superseded or deprecated, prepend a standard markdown alert notice at the very top of `notes.md` without modifying the rest of the text.
3. **Cryptographic Drift Audits (FR-19, FR-20)**: Source drift is measured deterministically using SHA-256 digests against baseline snapshots.
4. **Selective Course Evolution**: Learners can choose whether to adapt future unstarted chapters or maintain their existing course path.

---

## Workflow

### 1. Detect Source Drift

Execute the source drift inspection script for the target course:

```bash
uv run _tc/scripts/redirector.py diff-sources --path courses/<course_id>
```

The script inspects reference sources (e.g. in `plan/sources/` or `courses/<course_id>/sources/`), evaluates SHA-256 deltas, and cross-references them against `course.toml`.

### 2. Present Findings to Learner

Display the drift analysis clearly:
- **Modified Sources**: Documentation files that have changed since curriculum creation.
- **Added Sources**: Newly discovered guides or API specifications.
- **Affected Sections**: Unstarted or in-progress sections referencing modified sources.
- **Safe Completed Sections**: Sections already finished by the learner, whose notes remain intact.

Present the learner with explicit choices:
- `[1] Continue Current Trajectory`: Keep the current syllabus unchanged and ignore upstream source updates for now.
- `[2] Adapt Upcoming Sections`: Update lesson plans and objectives in pending chapters to reflect latest sources.
- `[3] Mark Deprecation Alert`: Prepend a notice to specific completed notes explaining that an upstream API or pattern has been superseded.

### 3. Non-Destructive Deprecation Protocol

If the learner requests deprecation of an existing completed section:

```bash
uv run _tc/scripts/redirector.py deprecate \
  --path courses/<course_id>/<chapter_dir>/<section_dir>/notes.md \
  --reason "Upstream library migrated from v1 to v2 syntax" \
  --redirect-to "courses/<course_id>/chapter-04/section-01"
```

The script prepends an alert block:
```markdown
> ⚠️ **Deprecation Notice**
> This material was superseded on YYYY-MM-DD.
> **Reason:** Upstream library migrated from v1 to v2 syntax
> **Redirect:** courses/<course_id>/chapter-04/section-01

[...Original learner notes preserved bit-for-bit...]
```

### 4. Course Notes State Inspection

To view the overall health and deprecation status of all notes in a course:

```bash
uv run _tc/scripts/redirector.py inspect --path courses/<course_id>
```

### 5. Next Action

Once drift triage is complete:
- If resuming an active section: run `/tc-teach`
- If testing a chapter: run `/tc-test-me`
