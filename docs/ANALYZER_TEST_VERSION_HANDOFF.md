# Analyzer test version: active work order

Decision date: 2026-09-14. User-authorized continuation in the existing shared
checkout; no new product checkout. This document records the current order of
work and supersedes older proposed three-application navigation for this task.

## Scope and priorities

1. Finish and integrate replay-round-integrity after explicit user takeover.
2. Add local CS2 minimap loading to the embedded Tactical 2D view, then perform
   a real visual review of an explicitly supported map/demo combination.
3. Prepare the final UI design and interaction states for review before UI
   implementation. PNG previews, editable sources and SVG assets may be used
   as appropriate; no implementation paths or framework choices in mockups.
4. Complete a functional Anubis 3D POV reference, including scene/player
   selection, playback/seek and consistent 2D/3D context. This is an intended
   outcome, not a claim that the present integrated build already meets it.

Benchmark map development is FROZEN until explicit user reactivation. Preserve
its sources and artifacts. Benchmark functionality belongs under the separate
Optimizer; no mandatory standalone Benchmark navigation is requested.

## Replay takeover

The user confirmed the previous worker was stopped and authorized takeover.
The four uncommitted replay changes were copied by reviewed patch into the
existing shared checkout based on 15a58d7. The stopped checkout is retained as
an archival source, not a continuing work branch. Its original files remain
untouched; uncommitted status there does not mean a second writer is active.

Verified WorkBridge snapshots of both the stopped checkout and shared checkout
were created before applying changes. They contain Git bundles, working files
and SHA-256 manifests on the existing backup drive. The existing session was
retargeted to the shared checkout following the authorized handoff.

The fix binds loaded round number, first/last tick and frame count to the
manifest descriptor after chunk validation and before caching. Invalid round
entries and invalid tick types produce validation errors instead of accidental
attribute/comparison exceptions. Tests exercise hash-valid mismatches, repeat
rejection without caching, empty frames and valid single/multi-frame rounds.

## Tactical 2D next slice

Update 2026-09-19: the first local minimap loading slice is implemented; see
TACTICAL_LOCAL_MINIMAP.md for actual tests, resource-load evidence and remaining
Windows visual acceptance. The following paragraphs describe its original scope.

The standalone HTML viewer already accepts a local radar image. The embedded
desktop canvas currently draws player-relative coordinates without a minimap.
The integration must use one shared transform for image and player markers,
including zoom/pan, and must not rebuild replay truth or parse the demo again.

Inspect the installed CS2 resources: image/texture plus the corresponding
overview descriptor. Reading game archives may require bounded extraction or
texture conversion into a user-local cache. Never copy game assets into Git or
the distributable package. Local reading alone is not a blanket rights grant.

Record map/resource identity and source revision where available. Unknown
demo/map version compatibility stays unknown; current installation does not
prove compatibility with an old demo. Missing resources retain a labelled
grid fallback. Never silently align a wrong image or infer vertical floors.

Existing numeric metadata covers Ancient, Mirage, Anubis and Dust2. This is
not a statement that all four have passed current visual acceptance. Choose
and record an actual map/demo/installation combination before claiming support.

## UI and community direction

Analyzer functions, custom filters, Tactical 2D, 3D POV, performance and reports
share a coherent work surface. Technical modules do not require separate tabs.
Preserve match, player, scene and timeline context. Optimizer has its own surface.

Use restrained Midnight/Metallic Blue from the references. Existing runtime
screens and older UI_SPEC.md navigation describe prior work; update their
authority explicitly when the new visual design is accepted. They must not
silently override this newer product direction or be treated as proof that the
new UI is implemented.

Proposed user-approved intent copy:

> Von der Community, für die Community. Improve Yourself entsteht aus Freude
> am gemeinsamen Entwickeln und Verbessern – ohne Gewinnerzielungsabsicht für
> diese Software. Feedback, Ideen und Beiträge sind willkommen.

This describes project intent, not a license grant or an implemented community
service. Do not create Discord infrastructure as part of this work order.

## Anubis acceptance and boundaries

Earlier blanket BLOCKED text in the 3D preflight is historical. Slice C records
a successful local-only geometry route; renderer/session work exists. Neither
proves today's visual integration or permission to distribute Valve geometry.
Revalidate assets and the fixed real reference scene on the target machine.
Keep geometry, timing and incomplete smoke evidence checks effective.

Accept only after real playback, seeking, selected-player POV, 2D/3D switching,
resource failure states and a repeatable tester setup have been checked. Keep
unsupported channels explicit. Obtain the user's additional 3D resource idea
before choosing a materially different distribution route.

## Maintenance and handoff

Reserve the last 20% of quota for verification, backups, reviewed commits,
GitHub comparison and handoff. Quota is supplied by the user, not measured here.
At each task end record actual results and outstanding work. Weekly maintenance
should review dirty worktrees, conflicting documentation, backup failures and
obsolete blockers; archive only after verified integration. This specifies the
routine but does not install another scheduler.

## Validation record

Update 2026-09-19: Windows execution now works. The shared checkout's locked
Windows setup and nine CLI smoke tests passed; full suite: **507 passed,
1 skipped**. An existing real Anubis workflow passed the current validator and
the application started with it. See TACTICAL_LOCAL_MINIMAP.md for the evidence
boundary and still-pending Windows local-resource/visual acceptance. The earlier
environment limitation below is historical, not an active blanket blocker.

Initial focused check: 34 tests passed using Python 3.13.15 / pytest 8.4.2 on
Linux against the shared checkout. Windows execution and real visual acceptance
are separate requirements; Windows Python cannot currently be launched from
this SSH environment.

Full suite with requirements.lock installed: one failure in the unchanged
`test_packaged_windows_default_output_is_stable_and_user_writable`, which
monkeypatches os.name to Windows and then attempts to instantiate WindowsPath
on Linux (UnsupportedOperation). Two tests skipped. This is not an all-green
Windows acceptance; rerun on Windows before tester distribution. Neither the
shell function nor that test differs from shared baseline 15a58d7.

The four transferred files match the stopped worker's contents after line-ending
normalization. No benchmark source or artifact was changed by this takeover.
