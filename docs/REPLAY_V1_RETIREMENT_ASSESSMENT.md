# Replay V1 retirement assessment

## Decision summary

**Retirement recommendation: retain `iy.replay/v1` temporarily; do not retire
it now.**

`iy.replay/v2` is the canonical integrated replay contract. The V1 contract is
not part of the canonical V2 Analyzer/Tactical/Desktop path, but it still has a
published, separately runnable local workflow and dedicated tests. Removing it
now would change supported runtime behavior without a replacement for that
workflow.

This is an assessment only. It neither deprecates a command at runtime nor
authorizes removal, migration, or a compatibility shim.

## Evidence-based dependency inventory

### Current dependencies that keep V1 alive

| Consumer | Current dependency | Why retirement is blocked |
| --- | --- | --- |
| `iy-workflow` | `workflow.py` calls the V1 `export_replay()` path and writes `iy.workflow/v1`. | It is a public CLI and produces the V1 replay artifact. |
| `Start-V1Review.ps1` | Starts `iy-workflow`, then `iy-review-server`. | It is the documented supported start for the isolated local V1 review workflow. |
| V1 review surface | `review.py` explicitly requires `iy.replay/v1`. | There is no demonstrated V2 equivalent for this legacy HTML review surface. |
| 2D viewer compatibility | `viewer.py` accepts both V1 JSON and V2 manifests. | Removing V1 would narrow a public viewer input contract. |
| Development baseline | `Setup-V1.ps1` smoke-tests `iy-workflow`; `pyproject.toml` publishes it. | Retirement must update the public entry-point and setup contract together. |
| Tests | `test_replay.py`, `test_workflow.py`, `test_review.py`, and V1 cases in `test_viewer.py`. | These are active regression coverage, not archival fixtures. |

### Canonical V2 consumers that do not depend on V1

- `iy-demo-workflow` produces `iy.replay/v2` via `replay_builder.py`.
- `AnalyzerCore` produces validated match data and `AnalyzerDataHub` distributes
  consumer projections without reading V1 replay artifacts.
- `ReplayStore` and `ReplayController` operate on the V2 manifest/chunks.
- Tactical Replay, embedded Tactical, renderer session, and the canonical
  Analyzer Shell use the V2 store/controller path.
- The dual-schema viewer constructs its V2 projection through `ReplayStore` and
  `ReplayController`; it does not route V2 input through V1.

## Historical-only material

The following documentation is historical design/progress context, not current
V1 runtime authority: the early 3D/POV preflight and Slice-A notes, the V1
prototype inventory, and prior migration plans that describe V1 as the active
foundation or propose evolving it into a full-match contract. The checked-in
canonical replacement for that proposed evolution is `iy.replay/v2`.

Historical material should remain readable for provenance, but must not be
used to justify restoring V1 as the active Analyzer/Tactical path or creating a
second parser, replay store, controller, or data hub.

## Required migration work before retirement

Retirement can be considered only after all of these conditions have evidence:

1. **Product decision:** decide whether the isolated V1 review experience is
   replaced by the V2 review/tactical flow or deliberately discontinued. This
   requires explicit product approval; it cannot be inferred from the presence
   of V2.
2. **Workflow replacement:** provide one supported V2-based replacement for
   the `iy-workflow` / `Start-V1Review.ps1` user journey, including equivalent
   local-only, source-bound, fail-closed review behavior where still required.
3. **Review migration or retirement:** migrate the V1-only `review.py` surface
   to a V2-backed contract, or formally retire that surface and its entry point.
   Do not make it parse V2 by bypassing `ReplayStore` or `ReplayController`.
4. **Viewer contract decision:** explicitly remove V1 input support from
   `iy-replay-viewer` only after the supported replacement and user migration
   are available. Preserve V2 construction through the canonical store and
   controller.
5. **Entry-point and documentation update:** update/remove the `iy-workflow`
   entry point, `Start-V1Review.ps1`, setup smoke expectations, README, and
   user-facing workflow documents in the same approved change.
6. **Regression evidence:** replace V1-specific tests with V2 replacement-path
   tests, retain V2 replay/store/controller invariants, and run the relevant
   full suite plus CLI smoke checks before deletion.
7. **Artifact policy:** define whether previously generated ignored V1 local
   artifacts remain readable for a transition window. No automatic discovery,
   conversion, deletion, or upload is authorized by this assessment.

## Safe retirement gate

V1 is safe to retire only when the team can demonstrate all of the following:

- no supported CLI, launcher, documentation path, or test still requires V1;
- the V2 replacement covers the intentionally retained V1 user workflow or an
  approved product decision has withdrawn that workflow;
- no canonical V2 consumer has gained a fallback, duplicate parser, store,
  controller, or data hub;
- generated V1 artifacts are handled by an explicit, local-first transition
  policy; and
- targeted and full validation pass after the approved runtime migration.

Until then, V1 should be described as **legacy-compatible and temporarily
supported**, while V2 remains the sole canonical replay truth for new
Analyzer/Tactical integration.

## Recommended next implementation task

Create a separately authorized, runtime-scoped **V1 workflow replacement
design**. It should first map user-visible requirements of `iy-workflow` and
`Start-V1Review.ps1` to existing V2 capabilities, identify any missing
fail-closed review behavior, and propose a migration test matrix. It must not
remove V1 or change the active V2 architecture until that design is approved.
