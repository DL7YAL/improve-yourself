# Improve Yourself — Design Reference

Status: BINDING VISUAL MASTER REFERENCE for the current Experimental/V1.1 consolidation.

This directory exists so implementation agents do not have to reconstruct approved UI decisions from chat history.

Read in this order:
1. `Improve_Yourself_Concept_Preview_Discord_Q98.pdf` — binding visual master reference.
2. `UI_SPEC.md` — visual language, layout rules and per-module targets.
3. `BRANDING.md` — product name, claim, wordmark/icon usage and tone.
4. `MOCKUP_INDEX.md` — page-by-page authority and what is binding vs illustrative.

## Authority

The checked-in nine-page PDF is the **visual master reference**, not optional inspiration. Its composition, logo treatment, dark Midnight/Metallic direction, information hierarchy, sidebar/navigation model, restrained technical character, tonal depth and blue light/reflection accents are binding visual decisions. Pixel coordinates, example numbers, example data, obsolete module labels and features superseded by current product decisions are not functional contracts.

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
