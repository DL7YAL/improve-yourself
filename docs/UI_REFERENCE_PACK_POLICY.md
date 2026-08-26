# UI Reference Pack Policy

Status: **binding reference hierarchy — Pack v1.0.0 verified locally**

## Authority order

1. The applicable `MASTER` screen in
   `Improve_Yourself_UI_Reference_Pack_v1.0.0.zip` controls that screen's
   visible content composition and visual target.
2. Variant 3 controls app-wide shell continuity: Improve branding, upper
   transition/header, left shell, navigation treatment and shared form
   language.
3. Current branch code controls functional truth, real data, safety boundaries
   and supported interactions.
4. Existing PDF/concept material is historical context only. It cannot
   override a Pack `MASTER` and must never be used to reconstruct a
   `SUPERSEDED` target.

## Required UI workflow

Before changing a screen, read the Pack README and manifest, confirm the file
classification, and inspect the corresponding `MASTER` image. `SUPERSEDED`
files are excluded from implementation.

For the Optimizer specifically, the only screen-level targets are:

- `optimizer_overview_MASTER.png`
- `system_optimizer_detail_MASTER.png`

The older PDF-derived Optimizer view is no longer an implementation target.

## Fail-closed reference access

If the Pack, README, manifest or applicable `MASTER` is inaccessible or
ambiguous, do not infer the target from an earlier PDF, screenshots, chat
memory or a prior build. Stop the UI task at `WAITING_FOR_TRISTAN` and request
the accessible reference source.

## Current workspace condition — 2026-08-22

The complete Reference Pack is now present at `docs/design/ui-reference/`.
`README_UI_REFERENCE.md` and the machine-readable
`UI_REFERENCE_MANIFEST.json` were read before the Optimizer/Shell pass. The
manifest was supplied inside the archived pack and is checked in alongside the
extracted references so the folder is complete at its documented location.

The three Optimizer image hashes match the manifest exactly:

- `optimizer_overview_MASTER.png` — `e2e91fdc…a4d6a004` — **MASTER**;
- `system_optimizer_detail_MASTER.png` — `4b0b5d5e…7b8bdb51` — **MASTER**;
- `optimizer_legacy_from_concept_pdf_SUPERSEDED.png` —
  `c6a47fd8…5973a3af3` — **SUPERSEDED**, excluded from implementation.

The PDF is not a fallback. The two MASTER PNGs are the only Optimizer screen
targets; Variant 3 remains binding only for the shared shell, branding, header
transition and navigation continuity.
