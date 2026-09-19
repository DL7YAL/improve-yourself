# Replay round integrity: IY-F01 and original IY-F02

STATUS: PASS for this bounded repair and its tests; not a whole-product acceptance.

Base: `b56aa3413480b1f082b4b2ef65346add7a1b1761`
Branch: `codex/replay-round-integrity`

## Changes

- IY-F01: the existing ReplayStore compares chunk round number, first tick, last tick and frame count with the manifest descriptor before caching. A mismatch raises ValueError; matching stores retain their existing behavior.
- Original IY-F02: the manifest validator reports non-object round entries and continues safely; tick ordering is compared only after integer type checks.
- Regression tests cover hash-valid mismatches, repeated rejected loads without cache insertion, empty frames, valid single/multiple frames, non-object entries and invalid tick types.

## Evidence

- Original before-fix regression run: 16 failed, 9 passed.
- Original corrected local run on Python 3.13.15: 39 targeted tests passed; full suite 451 passed, one optional azure.identity skip.
- User-supplied Azure report AZURE-REPLAY-ROUND-INTEGRITY-20260914-01: ten normalized file hashes matched; 25 isolated tests passed under Python 3.11.15 and pytest 8.2.2, exit 0. This is independent reviewer evidence supplied by the user, not a Codex-observed Azure execution or Python 3.13 product-suite result.
- Publication check on 2026-09-19: all ten base/candidate normalized hashes matched the reviewed manifest. The four implementation/test files remain identical to the audited candidate after UTF-8, CRLF-to-LF and final-newline normalization.
- Publication full suite: 451 tests passed, exit 0, using Python 3.13 and PYTHONPATH explicitly set to this checkout's src. Both replay module import paths were checked before execution.
- An initial publication test invocation without PYTHONPATH imported the old editable installation from a different checkout and failed 16 tests. It is not candidate evidence. Setting the process-local source path resolved the test-environment mismatch without product changes.
- Final whitespace, scope and secret checks are required before commit. Backups and exact remote commit equality are verified by the local WorkBridge finish operation.

## Continuation and boundaries

Use this branch's published commit as the immutable source identity for the next review. Set PYTHONPATH to the chosen checkout's src when reusing an existing virtual environment; verify imported module paths.

Canonical ReplayStore and replay validation remain the only implementation paths. No parser, controller, renderer or data hub was introduced; local operation remains cloud-independent and data boundaries are preserved.

AZURE-IY-EXPORT-01 remains a separate, unreproduced exporter finding. BM-F01 and all benchmark files are outside this change; BM-F03 remains PARTIAL / UNREVIEWED. No GUI, 2D/3D, CS2, visual, performance or whole-product acceptance is implied. No Azure settings, permissions, deployments or main-branch integration are part of this publication.
