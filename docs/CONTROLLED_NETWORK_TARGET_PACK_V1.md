# Controlled Network Target Pack V1

## Scope

`iy.network_target_pack/v1` is a versioned metadata catalog for the existing
read-only Network Quality Collector. Loading a pack never opens a connection.
Measurement starts only after an explicit target selection, a resolved host
and user confirmation.

## V1 catalog

The small reviewed V1 catalog contains one active target template:

| Target | Class | Why included | Scope |
| --- | --- | --- | --- |
| `local-gateway-template` | `LOCAL_GATEWAY` | The local gateway can provide an explicitly limited local-link observation once the user confirms its address. | Local connection only; no assertion about Internet, CS2 or FACEIT latency. |

No public or game-relevant host is included. Such a target was deliberately
rejected for V1 because there is no separately reviewed owner, stability,
purpose, disclosure and game-relevance contract. It must not be added by
guessing a generic public ping host.

## Required metadata and versioning

Every target carries a stable ID, display name, class, endpoint/template,
protocol, purpose, owner, privacy notice, expected disclosure, interpretation
scope, target version, validity window, status and technical prerequisites.
The pack itself has `pack_id` and `pack_version`.

An authorized `NetworkTarget` passes its `target_pack_version` into
`iy.network_quality_measurement/v1`; a historical session therefore retains
the target ID, class, target version and pack version even if a later pack
deprecates the target.

Only `ACTIVE` targets in their validity window can be selected.
`DEPRECATED` and `TEMPORARILY_DISABLED` targets stay interpretable for old
measurements but cannot start a new measurement.

## Consent and privacy contract

The future UI may use `selection_view_model()` before measurement. It exposes
the display name, target class, purpose, protocol, privacy notice and expected
disclosure and asserts both `requires_user_confirmation: true` and
`measurement_starts_automatically: false`.

The V1 gateway target has no embedded host. The caller must provide a local
address and explicitly confirm it. Results remain local under the existing
collector policy; no public IP, MAC address, telemetry or result upload is
added.
