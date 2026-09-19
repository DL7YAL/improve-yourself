# Local CS2 minimap: implementation and acceptance

Date: 2026-09-19. Shared checkout; benchmark map development remains frozen.

The embedded Tactical canvas now offers **Lokale CS2-Karte laden** after a
scene is opened. Select the local CS2 installation and the Source 2 Viewer CLI
executable. The application reads exactly the selected map's overview descriptor
and compiled radar texture through that executable. Conversion runs in a worker
thread with a timeout; no game archive is changed. Temporary exported files are
removed after loading. No Valve images or converter binary are shipped in Git.

Source 2 Viewer CLI 20.0 is the version exercised in this slice. Install the
appropriate platform build from the official project's releases; the application
does not silently download an executable. Upstream CLI options are documented at
https://s2v.app/ValveResourceFormat/guides/command-line.html.

## Presentation contract

- Map pixels and canonical player positions share one projection, zoom and pan.
- The overview uses north-up presentation; a Source presentation rotate flag
  is not treated as intrinsic coordinate rotation.
- Local numeric metadata must match the existing verified projection contract.
- Supported metadata candidates: Ancient, Mirage, Anubis, Dust2. Unknown maps,
  changed transforms, duplicate keys, unsupported nested layer descriptions,
  non-finite values and unexpected image dimensions are rejected.
- The source archive-index, descriptor and converted image hashes are recorded
  in the in-memory result. An index change during reading rejects that load.
- These checks do not prove the installed revision matches a historical demo.
  The UI states **Demo/Kartenversion nicht abgeglichen · Ebenen nicht geprüft**.
- A failed load leaves the labelled relative grid fallback, never a stale image.
- Opening another workflow clears the image; a late worker result is discarded
  if the active Tactical session has changed. No new parser or playback authority.

## Evidence and remaining acceptance

Focused tests: 27 passed (local loader, embedded Tactical and existing viewer),
Python 3.13.15 with requirements.lock. Tests cover malformed descriptors,
projection anchors with zoom/pan, targeted extraction, temporary-file cleanup,
conversion failure/timeout, changed source and wrong image dimensions.

Real installed Anubis resources successfully loaded using CLI 20.0.6980:
1024x1024 PNG, origin (-2796, 3328), scale 5.22. Converted PNG SHA-256:
`b8f07c36edb13e34dbfaabf9a74e057961ac4fb29545d98d16ff9b7c4e6d1206`.
This is resource-load evidence, not a visual replay acceptance or demo-version
compatibility proof. The application performs no legal rights inference.

Ancient and Mirage also passed real resource loading with their expected
projections. Dust2 was explicitly rejected: the installed descriptor references
`overviews/de_dust2_v2`, not the assumed material for `de_dust2`. Resolve and
verify that resource association before enabling it; no guessed image is shown.

Full suite: 504 passed, 3 skipped, 1 failed. The failure is the previously
recorded WindowsPath test under Linux; the relevant function is unchanged.
This is not a Windows release or visual acceptance.

Windows visual acceptance remains required: open a real matched Anubis workflow,
load its local map, inspect known landmarks/player alignment, seek and change
scenes, zoom/pan/reset, switch workflows, and test missing resources. Confirm
responsive loading and unchanged review/scene context. No visual pass is claimed.

### Windows follow-up, 2026-09-19

Windows process execution is now available from the shared workspace. The
existing Setup-V1 script installed the locked dependencies in this checkout's
Windows .venv; dependency consistency and all nine CLI help smoke tests passed.
Full Windows suite against source commit `4f9edad36885aa7903039cfe118bce79f13a4146`:
**507 passed, 1 skipped in 13.48 seconds**, Python 3.13.15 / pytest 8.4.2.
The previously failing Linux WindowsPath test passes on Windows.

An existing real Anubis workflow passed the current fail-closed validator,
including loading and validating its replay rounds. Its source-demo SHA-256 is
`922802f4d8796178f609ec134975f550dad8d905b4fbee3098a40b3ec8064d8d`.
The existing workflow was read in place, not copied or reparsed. The shared
checkout's application was launched with it; Windows reports an
`Improve Yourself - Experimental` window and the startup error log is empty.
This proves process/window startup, not visual correctness or demo/map revision
compatibility. No Windows converter was located in the searched tool locations;
selecting a verified Windows Source 2 Viewer CLI and the visual checks above
remain outstanding. Linux resource-load evidence does not replace these checks.

The final UI design and functional Anubis 3D POV remain subsequent work as
specified in ANALYZER_TEST_VERSION_HANDOFF.md. This slice adds only the actual
2D map loading control; it does not preempt the final visual design.
