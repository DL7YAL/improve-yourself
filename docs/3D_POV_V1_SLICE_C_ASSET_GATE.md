# 3D / POV V1 — Slice C Anubis Asset Gate

Status: `BLOCKED — product/licensing route required`

Date: 2026-08-20

No map geometry was copied, extracted, converted, committed or accepted during this gate. No renderer work began.

## Candidate inventory

### Awpy triangle candidate

- local path class: user-local Awpy cache, not repository content;
- source: Awpy 2.0.2 downloadable `tris` artifact;
- source build: CS2 build `17595823`, dated 2025-03-04 according to Awpy's installed artifact registry;
- file: `de_anubis.tri`;
- size: 29,088,000 bytes;
- SHA-256: `3DA37BBC33A9E9B2C469E9E39F1FF0A31A6EFE4212D10026516C803B708D9787`;
- triangles: 808,000;
- bounds: X `-3202.5049..2816.5098`, Y `-3456..4736`, Z `-704..1012`;
- render materials/semantics/dynamic geometry: absent;
- distribution: unresolved; Awpy code is MIT, but that does not itself establish redistribution rights for game-derived geometry;
- gate result: `version_mismatch`, not accepted.

Technical coordinate evidence against real replay source `446eec75822c…`:

- all 2,523,998 observed player positions fall inside the triangle bounds;
- replay bounds: X `-1971.9473..1803.9713`, Y `-1759.9688..2771.7646`, Z `-191.9688..188.1563`;
- identity transform is therefore numerically plausible, but not visually/current-build verified;
- Awpy BVH controlled visible pair at round 1/tick 6401: `(-259.6265,-1595.3811,52.0313)` to `(-508.1600,-1589.8218,66.0312)` -> visible;
- controlled blocked pair at the same tick: `(-259.6265,-1595.3811,52.0313)` to `(-527.9521,2207.1423,89.0313)` -> blocked;
- these checks prove the old candidate can answer LOS in replay coordinates; they do not prove parity with current CS2 geometry.

### Installed current Valve candidate

- installed CS2 App 730 build: `24828357`;
- installed map file: `game/csgo/maps/de_anubis.vpk`;
- size: 269,890,099 bytes;
- SHA-256: `BCA91CEE11592C65C2869C599769232F29335458376ED90431A013B58C938E07`;
- companion `de_anubis_vanity.vpk`: 8,430,194 bytes;
- companion SHA-256: `2943FBDB7A7261F65CB7CA47E6C1CF4B910D1B52D281BCCEC019A49121967C39`;
- map extraction/conversion was not performed;
- no approved render/visibility derivative or transform proof exists;
- gate result: `distribution_blocked` until an explicitly approved local-only or derivative route is selected.

## Distribution finding

Awpy's package/code carries an MIT license, but the candidate triangle artifact represents Counter-Strike map geometry. The Steam Subscriber Agreement reserves Valve content rights and limits copying, derivative creation and distribution unless an applicable permission or separate term allows it. It separately permits content created with Valve Developer Tools on a non-commercial basis and directs commercial Developer Tools use to Valve. This engineering gate is not legal advice and does not infer a commercial redistribution grant.

Therefore neither candidate meets every V1 acceptance rule:

- old Awpy `.tri`: coordinate/LOS-capable but stale and distribution-unresolved;
- installed VPK: current and hashable, but not an accepted mesh and not approved for extraction/distribution.

`map_geometry` remains `unavailable`; the product must show `3D POV für diese Map nicht verfügbar: Kartenasset nicht freigegeben.`

## Machine-enforced gate

`map_assets.py` implements `iy.map_asset/v1` assessment with explicit outcomes:

- `available`;
- `missing`;
- `version_mismatch`;
- `integrity_failed`;
- `distribution_blocked`;
- `unsupported_map`.

It rejects wrong schema/map, unapproved distribution, unverified version status, incomplete transforms, missing files, path escape and SHA-256 mismatch. Synthetic tests do not include Valve data.

## Decision required

Tristan must choose one permitted route before Slice C can complete:

1. authorize a current-build, local-only extraction/derivative that is never committed or distributed, then validate transform, known points and LOS locally;
2. provide or approve a distributable controlled derivative with documented rights;
3. keep Anubis 3D unavailable until an acceptable asset exists.

No renderer, camera, player proxy or sightline implementation may begin before this decision and the resulting asset passes the complete gate.
