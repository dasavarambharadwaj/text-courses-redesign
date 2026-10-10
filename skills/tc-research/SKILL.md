---
name: tc-research
description: "Scout technical documentation and extract structured ToC, API indexes, and vocabulary digests."
---

# `tc-research`: Technical Documentation Scout & Research Caching Engine

`tc-research` serves as the Scout in the Triad Consensus Loop. It verifies factual technical ground truth against official documentation sources, preventing hallucinated APIs, deprecated patterns, and inaccurate prerequisites.

## Core Invariants

1. **Grounded Source Research (FR-6)**: Curriculum topics must be grounded in verified documentation, API references, or authoritative source trees.
2. **Confidence Scoring**: Every scouted digest must carry an explicit confidence rating:
   - `high`: Verified against official documentation URLs or authoritative source files.
   - `medium`: Inferred from secondary references or partial extracts.
   - `low`: Incomplete or fragmented notes.
   - `unverified`: Synthetic topic fallback without external documentation ground truth.
3. **Deterministic Research Cache (AD-4)**: Scouted artifacts are persisted deterministically into `.tc/research/<slug>/digest.json` and `.tc/research/<slug>/sources.toml`.
4. **Zero Course Directory Pollution**: `tc-research` strictly populates `.tc/research/` and never writes directly into `courses/`.

---

## Workflow

### 1. Ingest Documentation Sources

Run the scout against an official documentation URL, a local directory, or a source file:

```bash
# Ingest local documentation tree
uv run _tc/scripts/scout.py scout --slug tokio-async --source-path plan/sources/tokio_docs/

# Ingest official documentation URL
uv run _tc/scripts/scout.py scout --slug react-hooks --url https://react.dev/reference/react

# Fallback topic exploration
uv run _tc/scripts/scout.py scout --slug database-internals --topic "Database Storage Engines and B-Trees"
```

The scout extracts:
- Table of Contents (`toc`): Headings, modules, chapters.
- API Index (`api_index`): Functions, methods, classes, types, structs, signatures.
- Vocabulary (`vocabulary`): Technical terms, keywords, and primitives.

### 2. Inspect Cached Digest

Retrieve the scouted digest for review or pipeline consumption:

```bash
uv run _tc/scripts/scout.py get --slug tokio-async
```

### 3. List Research Topics

List all cached research digests across the workspace:

```bash
uv run _tc/scripts/scout.py list
```
