# Viewer product map asset boundary

Generated collision/map previews are tooling and debug artifacts only.

They are not product map artwork, are not Viewer default backgrounds, are not geometric authority, and do not establish redistribution rights.

The canonical coordinate/projection authority remains `resources/map_overviews/maps/<map_id>.json`.

A Viewer product background must be supplied from an approved, project-owned map asset path. If no approved product map is available, the Viewer must report the background as unavailable instead of silently falling back to `resources/generated_overviews/**`.

Experimental map-generation work, including PR #26, remains independent tooling/research and is not a dependency of the Viewer product path.
