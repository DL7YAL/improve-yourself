# CS2 Workshop benchmark asset-rights and branding boundary

Status: **LOCKED PROJECT POLICY**

Owner decision: 2026-09-05

This document records the implementation boundary chosen by the project owner.
It is not a transfer of rights, a representation of ownership, or legal advice.

## Rights remain with Valve and the respective rights holders

Improve Yourself acquires no ownership, copyright, trademark, sublicensing, or
independent redistribution rights in Counter-Strike 2, Valve maps, models,
materials, textures, sounds, particles, names, marks, or other game content.
Those rights remain with Valve and/or the respective rights holders.

Use through the official CS2 Workshop Tools is a limited use inside the Steam,
CS2, and Workshop context under the applicable Valve/Steam terms. It must never
be described as ownership by Improve Yourself or as a general license to reuse
Valve content outside that context.

Official terms checked when this policy was recorded:

- Steam Subscriber Agreement, especially sections 2.A, 2.C, 2.D, 2.F, 2.G,
  and 6.B: <https://store.steampowered.com/subscriber_agreement/Valve?l=english>
- Counter-Strike 2 Workshop terms:
  <https://steamcommunity.com/workshop/workshoplegalagreement/?appid=730>

Terms can change. The current terms and the intended distribution model must be
reviewed again before publication, monetization, commercial integration, or any
distribution outside the CS2 Workshop context.

## Binding Workshop implementation rule

The benchmark is authored as a CS2 Workshop addon. The original CS2 maps are
the sole visual, spatial, and workload references for the corresponding scenes:

- `nuke_outside`: original Nuke Outside;
- `ancient_b`: original Ancient B, including the water/ramp and Red Room route;
- `inferno_apps_a`: original Inferno Apps / Second Mid / A approach.

For visual authenticity and representative CS2 rendering load, the Workshop
map may reference original Valve/CS2 models, materials, textures, particles,
and other assets that are available through the installed game and the official
CS2 Workshop Tools. Prefer canonical runtime references to installed CS2 assets.

This permission is limited by all of the following rules:

1. Do not extract Valve assets from VPKs for this workflow.
2. Do not copy Valve source or binary assets into this repository.
3. Do not present Valve assets, map design, names, or marks as Improve Yourself
   property.
4. Do not repackage Valve assets in an Improve Yourself installer, portable ZIP,
   standalone viewer, independent 3D world, or separately downloadable asset
   bundle.
5. Do not use a Valve asset outside CS2 merely because the Workshop map can
   reference it inside CS2.
6. Do not imply that Valve developed, certified, endorsed, or sponsors the
   benchmark.
7. Third-party assets remain blocked unless their rights, license, provenance,
   and intended distribution are separately verified.
8. Unknown ownership or origin is fail-closed: the asset is not used until the
   uncertainty is resolved.

Compiled local test output and any future Workshop submission remain separate
from the standalone Improve Yourself application. The application may identify
or launch the separately installed Workshop benchmark only through a later,
explicitly reviewed integration contract; it must not carry the Valve assets.

## Improve Yourself identity

The benchmark must be recognizably authored and orchestrated by Improve
Yourself without obscuring Valve's ownership or suggesting endorsement. Use the
canonical Variant 3 Improve Yourself branding for project-authored elements.

Project-authored identity may include:

- Improve Yourself logos, signs, decals, labels, and benchmark markers;
- benchmark route, deterministic scene orchestration, transitions, and timing;
- measurement presentation and project-authored controller logic;
- original supplemental geometry, materials, and props with recorded
  provenance.

Project branding must use its own namespace and files. It must not overwrite,
modify, relabel, or masquerade as a Valve asset. The visible combination of
Valve-owned CS2 content and Improve Yourself branding does not change the
ownership of either category.

A publication candidate must carry a clear non-affiliation notice substantially
equivalent to:

> Unofficial community benchmark for Counter-Strike 2. Not affiliated with or
> endorsed by Valve Corporation. Counter-Strike, Counter-Strike 2, Steam,
> Valve, and associated game assets and trademarks remain the property of
> Valve Corporation and/or their respective rights holders. Improve Yourself
> branding, benchmark orchestration, and independently created supplemental
> content are attributable to Improve Yourself.

The exact public wording remains subject to final legal and release review.

## Required asset provenance record

Every visually relevant asset introduced during the Nuke, Ancient, or Inferno
authoring passes must be classified before the scene can be approved:

| Field | Requirement |
| --- | --- |
| `scene` | `nuke_outside`, `ancient_b`, or `inferno_apps_a` |
| `asset_path` | Exact Workshop Tools / addon reference path |
| `rights_class` | `VALVE_RUNTIME_REFERENCE`, `IMPROVE_ORIGINAL`, or `THIRD_PARTY_VERIFIED` |
| `source` | Installed CS2 path/build, canonical Improve source, or licensed third-party source |
| `purpose` | Visual and benchmark workload role |
| `distribution` | `CS2_WORKSHOP_RUNTIME`, `PROJECT_DISTRIBUTABLE`, or another explicitly reviewed value |
| `evidence` | Build/version plus hash or license/provenance evidence where applicable |

`VALVE_RUNTIME_REFERENCE` must resolve through the installed CS2/Workshop Tools
environment and must not point to a copied repository asset. `IMPROVE_ORIGINAL`
must identify the canonical project source and its provenance. A missing or
ambiguous classification blocks release approval.

## Nuke Outside application gate

The next visual authoring pass may implement `nuke_outside` directly from the
original Nuke Outside reference and may use original CS2 runtime assets under
this policy. The pass must:

1. preserve the existing deterministic benchmark route and transition contract;
2. reproduce the relevant visual and workload characteristics rather than
   inventing an unrelated environment;
3. keep all Improve Yourself branding project-authored and visibly distinct;
4. add or update the asset provenance record for every introduced reference;
5. avoid extraction, repository copies, independent packaging, and ownership
   claims;
6. run a fresh Full Compile, marker-correlated visual review, and performance
   baseline after the visual scene is complete.

Technical success does not by itself constitute legal or release approval.
