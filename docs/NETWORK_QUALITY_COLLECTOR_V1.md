# Network Quality Collector V1

## Boundary

`iy.network_quality_measurement/v1` is a local, read-only observation record.
It changes no MTU, DNS, RSS, EEE, interrupt moderation, offload, power
management, TCP/IP, registry, firewall or route. It has no recommendation or
apply authority.

Targets are mandatory command arguments, versioned and recorded with their
purpose. Supported classes are `LOCAL_GATEWAY`, `CONTROLLED_PUBLIC_TARGET` and
`GAME_RELEVANT_TARGET`. A public target is never represented as actual CS2 or
FACEIT quality by default.

## Method

The current Windows method uses one ICMP echo request per declared sample.
Each record stores target, method/protocol, sample count, interval, timeout,
timestamp, session ID, successful/failed probes and local adapter context.

- RTT distribution: successful individual RTT samples, min, max and mean.
- Jitter: mean absolute difference between consecutive successful RTT samples.
- Packet loss: failed requested samples / requested samples, only if the target
  answered at least once.

No answer from a target is `TIMEOUT`, `TARGET_UNREACHABLE` or
`BLOCKED_OR_FILTERED`, not customer-connection packet loss. Fewer than three
successful samples is `TOO_FEW_SAMPLES`; it still records the observation but
is not a quality conclusion.

## Privacy and integration

Results are written only to the caller-chosen local output file. They set
`external_transfer: false` and `public_ip_persisted: false`. Adapter context is
minimized to operational fields; MAC addresses are deliberately not persisted.

`network_quality_evidence()` turns a record into an `EVIDENCE_RECORD` with
source type `OBSERVED_NETWORK_QUALITY`. It explicitly states that correlation
is not configuration causation. The shared Recommendation Engine does not
create a recommendation from this collector alone.

`measurement_session_id` allows later BEFORE/AFTER comparison after a
separately authorized change, without implementing that change now.

## CLI example

```powershell
iy-network-quality --target-id local-gateway --target-class LOCAL_GATEWAY --host 192.168.1.1 --purpose "Declared local gateway check" --output results/network-quality.json
```

The operator, not Improve Yourself, chooses and declares the target. The tool
does not resolve or discover an external target automatically.
