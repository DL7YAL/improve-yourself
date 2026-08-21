# Improve Yourself — Design Reference

Status: CANONICAL DESIGN DIRECTION for the current Experimental/V1.1 consolidation.

This directory exists so implementation agents do not have to reconstruct approved UI decisions from chat history.

Read in this order:
1. `UI_SPEC.md` — visual language, layout rules and per-module targets.
2. `BRANDING.md` — product name, claim, wordmark/icon usage and tone.
3. `MOCKUP_INDEX.md` — approved concept-preview screens and what is binding vs illustrative.

## Authority

The approved Concept Preview screens are design targets, not pixel-perfect implementation contracts. Their composition, dark Midnight/Metallic direction, information hierarchy, sidebar/navigation model and restrained technical character are binding. Example numbers, example data, obsolete module labels and features superseded by current product decisions are not binding.

If current functional requirements conflict with an old mockup, preserve the current function and adapt it to the design language. Do not resurrect removed features just because they appear in a concept image.

If a screen is not sufficiently specified, keep the existing functional implementation and mark `NEEDS_UI_REFERENCE`; do not invent a new visual language.

## Product principle

Improve Yourself is an analysis and improvement tool, not a statistics clone and not a black-box verdict system. UI should make data origin, rules and review flow understandable while keeping the number of user decisions deliberately small.
