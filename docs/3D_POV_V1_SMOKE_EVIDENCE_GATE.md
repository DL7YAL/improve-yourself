# 3D/POV V1 — smoke evidence gate

Date: 2026-08-21

## Result

`CanonicalSmokeEvidence` can return `clear` or `blocked` only when canonical utility lifetime/position coverage is explicitly `full`. `partial` and `unavailable` return `unknown` before any volume test, even when the current frame lists no active smoke.

The fixed V1 analytical approximation is a sphere with radius 144 Source Units around each active, lifetime-evidenced smoke position. This is a disclosed conservative visualization/evaluation approximation, not a claim that CS2 smoke is a perfect sphere or that 144 is an engine truth. The radius is not written into replay state.

With full coverage:

- every active smoke must have position, start tick, end tick and `lifetime` evidence;
- the canonical frame tick must be inside that evidenced lifetime;
- segment distance below or equal to 144 Source Units returns `blocked`;
- tangent contact is blocked;
- no active intersection returns `clear`;
- any inconsistent active smoke downgrades the query to `unknown`.

Every reason string discloses the sphere approximation and radius when it is applied, or states why it was not applied.

## Real Anubis validation

The real Anubis replay manifest reports `utility_lifetimes=partial`. At round 1/tick `6401`, the nearby geometry-clear pair therefore remains:

- geometry: clear;
- smoke: unknown;
- final result: unknown.

The frame contains zero active smoke entries, but partial whole-replay coverage cannot prove that none is missing. The gate correctly refuses to convert absence in that frame into evidenced smoke-clear visibility.

## Validation

- focused sightline/smoke tests: 15 passed;
- complete repository suite: 91 passed;
- intersection, non-intersection and exact tangent tests: PASS;
- partial/unavailable and malformed-full downgrade tests: PASS;
- real Anubis partial-capability proof: PASS, approximation not applied;
- full Setup-V1 and five public CLI smoke checks: PASS.

## Boundary

No smoke mesh, particle, utility/event overlay, renderer change, inferred lifetime, asset packaging, benchmark change or second replay interpretation was added.

## NEXT

Implement only the controller-to-renderer session adapter: consume `ReplayController` snapshots, restore the canonical typed frame, map the existing FP/fixed-TP view modes, and update selected player/frame without owning playback or parsing. Prove seek, player selection and FP/TP switching preserve requested/resolved tick semantics. Do not add a product UI, smoke rendering, utility/event overlays or another state authority.
