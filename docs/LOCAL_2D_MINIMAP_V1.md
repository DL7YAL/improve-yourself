# Local 2D Minimap V1

The Tactical Replay can display explicitly selected local PNG map surfaces
behind its canonical player projection. The repository and ordinary public
package contain no map artwork.

## Authority boundary

The image is presentation only. Map ID, tick, scene, playback, and player state
continue to come from the existing path:

```text
AnalyzerCore -> AnalyzerDataHub -> iy.replay/v2 -> ReplayStore
             -> ReplayController -> Tactical Replay
```

World-to-overview coordinates come only from the matching verified
`resources/map_overviews/maps/<map_id>.json` document. A local image never
supplies a transform and never makes an unavailable map available.

The initial registration value is
`FULL_OVERVIEW_CANVAS_UNVERIFIED_LOCAL_TEST`. It fits the complete PNG to the
logical overview canvas and remains visibly labelled as technically
unverified. It is not evidence that the artwork is geometrically correct or
approved for public distribution.

## Internal-only manifest

Store the manifest and its images together outside the repository:

```json
{
  "schema": "iy.local_test_map_surfaces/v1",
  "distribution": "LOCAL_ONLY",
  "surfaces": {
    "de_ancient": {
      "path": "images/de_ancient.png",
      "sha256": "<lowercase SHA-256>",
      "registration": "FULL_OVERVIEW_CANVAS_UNVERIFIED_LOCAL_TEST"
    },
    "de_anubis": {
      "path": "images/de_anubis.png",
      "sha256": "<lowercase SHA-256>",
      "registration": "FULL_OVERVIEW_CANVAS_UNVERIFIED_LOCAL_TEST"
    }
  }
}
```

Every path must be relative and stay under the manifest directory. The loader
accepts only PNG files up to 32 MiB and 8192 pixels per axis, verifies the
SHA-256 hash, and rejects missing, changed, absolute, escaping, malformed, or
wrongly classified inputs. Rejection falls back to the verified image-free
projection; it never guesses a map transform.

Start an internal session explicitly:

```powershell
tools/dev/Start-Experimental.ps1 `
  -Workflow '<local workflow>/demo-workflow.json' `
  -LocalMapSurfacesManifest '<private assets>/local-map-surfaces.json'
```

The environment variable
`IMPROVE_YOURSELF_LOCAL_MAP_SURFACES_MANIFEST` is scoped to that launched
process and restored afterwards. An ordinary start performs no scan and does
not discover local map images automatically.

## Packaging boundary

The packaged application includes the nine numeric map-overview metadata
documents so the canonical projection remains available. It does not include
the local manifest or any PNG map surface. For the authorised internal tester
candidate, the private map folder must be delivered separately and selected
explicitly. Public candidates must omit it until a separate release-specific
rights gate is approved.
