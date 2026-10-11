# Story 4: Resilient Cross-Platform Hash Checksum Normalization

**Status**: completed  
**Covers**: FR-41  
**Prerequisites**: Story 1  

## Context & Objectives
Prevent false-positive course tampering warnings triggered by operating system newline variations (CRLF vs LF) or trailing whitespace cleanup in git.

## Implementation Steps
1. In `_tc/scripts/hash_tracker.py`, implement `normalize_content_for_hashing(content: bytes | str) -> bytes`.
   - Convert CRLF (`\r\n`) and CR (`\r`) to LF (`\n`).
   - Strip trailing whitespace from each line while preserving code indentation and semantics.
2. Apply `normalize_content_for_hashing` across `compute_file_hash` and `verify_file_hash`.
3. Update `auditor.py` to use normalized hashing when checking note and manifest integrity.
4. Verify with unit tests in `tests/test_hash_normalization.py` testing identical SHA-256 hashes for CRLF vs LF strings.
