# Improve Yourself — Design Reference

Status: **Canva revision 25 is the binding visual authority.**

Read `CANVA_UI_AUTHORITY_CANDIDATE.json` and
`CANVA_UI_MIGRATION_HANDOFF.md` first. Canva design `DAHUBn5D2aM`
(`Versuch.nr1`) is the sole visual source. The old UI Reference Pack, its
`*_MASTER.png` files, the concept PDF and the former Optimizer package are
SUPERSEDED and must not be implemented.

This directory exists so implementation agents do not have to reconstruct approved UI decisions from chat history.

Read in this order:
1. `Improve_Yourself_UI_Reference_Pack_v1.0.0.zip` — its
   `README_UI_REFERENCE.md`, `UI_REFERENCE_MANIFEST.json`, then the applicable
   `MASTER` screen image. This is the visual authority when the pack is made
   available to the workspace.
2. Variant 3 in `BRANDING.md` — the authority for the global shell, upper
   transition/header, Improve branding and shared navigation treatment.
3. `UI_SPEC.md` — shared visual language and current functional constraints.
4. `MOCKUP_INDEX.md` — legacy concept-page mapping and non-master context.

## Authority

The UI Reference Pack is the central visual authority. Only files classified as
`MASTER` in its manifest may be implemented as a screen target. Files marked
`SUPERSEDED` are explicitly excluded from implementation. For the Optimizer,
`optimizer_overview_MASTER.png` and `system_optimizer_detail_MASTER.png`
supersede the earlier PDF-derived target.

Variant 3 remains the global authority for the upper shell, header/transition,
logo treatment, left shell and shared navigation. A screen `MASTER` controls
that screen's content composition; Variant 3 controls the shared shell where
the two overlap.

The checked-in nine-page PDF is retained as historical concept context only.
It must not be used to reconstruct, infer or override a superseded screen.
If the applicable Reference Pack archive or its required `MASTER` is missing,
unclear or inaccessible, stop the UI task with `WAITING_FOR_TRISTAN` rather
than deriving a new target from the PDF, memory or an older implementation.

Two truths apply together:

- the current branch is the functional truth;
- the PDF is the visual truth.

Neither truth may silently replace the other. A visual alignment must preserve current real data, safety boundaries and tested workflows. A functional change may not introduce a competing visual language.

If current functional requirements conflict with an old mockup, preserve the current function and adapt it to the design language. Do not resurrect removed features just because they appear in a concept image.

If a screen is not sufficiently specified, keep the existing functional implementation and mark `NEEDS_UI_REFERENCE`; do not invent a new visual language.

## Current conformance checkpoint

The Experimental shell already conforms on Variant-3 branding, dark application chrome, persistent sidebar, restrained cyan accents, tonal cards, clear hierarchy and the absence of white foreign surfaces. Remaining visible deltas to the master are flatter surfaces, less metallic depth, fewer subtle reflection/light cues, sparse iconography and lower panel density. These are documented visual follow-ups, not permission to fabricate data, controls or functions.

## Product principle

Improve Yourself is an analysis and improvement tool, not a statistics clone and not a black-box verdict system. UI should make data origin, rules and review flow understandable while keeping the number of user decisions deliberately small.
