# Codex

STATUS: partial
TASK: Visually verify the existing Nuke Outside graybox against the runtime camera
BRANCH: `dev/v1-foundation`
CHANGED: Only this handoff; no Hammer source, scene geometry, camera, utility, or smoke position was changed
VERIFIED: Steam launched the existing CS2 Workshop Tools addon `improve_yourself_benchmark`; Hammer opened `improve_yourself_benchmark.vmap`; the existing compiled map was loaded through `Run (Skip Build)`. Runtime observation confirmed that the smoke wall obscures nearly the entire Nuke camera image for most of the segment. During the late Nuke view only a thin geometry silhouette remains visible at the top edge, so Red/Main/Secret massing cannot yet be evaluated reliably from the intended camera. The prior controller validation remains green (`3 scenes`, `4097` sampled 64 Hz camera poses), and the last documented Hammer build remains `23 compiled, 0 failed`.
DECISIONS: No new product decision and no scene adjustment. The runtime evidence confirms the already documented ordering: clear the camera occlusion before judging or aligning the Nuke masses.
OPEN: The exact first-smoke displacement still needs a controlled implementation pass followed by a rebuild and the same runtime-camera check. The optimizer benchmark's authoritative Hammer sources remain in the local CS2 addon workspace and are not yet imported into this repository.
NEXT: Move only the first Nuke smoke wall far enough out of the early camera corridor to preserve a visible buildup, then rebuild and repeat the runtime-camera check before changing any Nuke geometry.
COMMIT/PR: Analyzer foundation `3e03875`; initial synchronization `e0aebe1`; visual-check handoff commit follows on `dev/v1-foundation`
