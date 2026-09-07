# Standalone Benchmark Result V1

## Product boundary

The CS2 Benchmark Map is an independent local product area. It does not import,
feed or evaluate Optimizer, System Check, Analyzer, Demo or Replay data.

```text
explicit local frame capture + explicit local CS2 controller log
    -> fail-closed validation
    -> iy.cs2_benchmark_result/v1
    -> local run history
    -> personal local top 10 for the identical benchmark/profile key
    -> self-contained local result page
    -> optional screenshot taken and shared by the user
```

There is no upload, account, Steam ID, Discord integration, telemetry or
automatic sharing. The application does not post results. A screenshot is
created and shared, if at all, by the user through their own operating-system
and communication tools.

## Capture input

`iy.cs2_benchmark_capture/v1` is an explicit normalized input from a separate
local frame collector. The collector is not bundled or silently discovered.
The capture must contain:

- a safe local `run_id` and timezone-qualified capture timestamp;
- exact benchmark version, VMAP hash, controller hash, pass length and route;
- a named graphics profile plus the SHA-256 of its settings definition;
- collector ID/version, `cs2.exe` process binding, start/end timestamps and an
  explicit active-capture confirmation;
- a local-only/no-external-transfer policy;
- contiguous, monotonic per-frame samples with elapsed time and frametime.

No player name, Steam ID, account ID, IP address, absolute path, hardware
serial number or Optimizer field is part of the contract.

## Validation

A result is `VALID` only when all gates pass:

1. exact input shape and schema;
2. exact V1.2 VMAP/controller hashes, locked route and 64-second pass;
3. complete latest controller session;
4. five measured capture windows in the expected order;
5. three measured scene reports in route order;
6. measured-pass runtime completion and no `[IYBENCH] ERROR`;
7. confirmed active collector bound to `cs2.exe`;
8. local-only policy;
9. at least 120 finite positive samples;
10. monotonic timeline, complete route coverage and agreement between elapsed
    timestamps and summed frametimes.

An invalid result retains its reasons but exposes no aggregate or scene
performance values and is never eligible for the top 10.

## Metric definitions

- average FPS: `1000 * frame count / summed frametime milliseconds`;
- 1% low FPS: `1000 / mean(slowest ceil(frame count * 1%) frametimes)`;
- frametime mean: arithmetic mean;
- frametime P95/P99: nearest-rank percentile;
- maximum frametime: maximum observed frame sample.

Scene summaries use the controller's locked windows: Nuke `[0,22)`, Ancient
`[22,43)` and Inferno `[43,64]` seconds.

## Comparison and local history

Runs are comparable only when all of these values are identical:

- benchmark version;
- VMAP SHA-256;
- controller SHA-256;
- graphics profile ID;
- graphics-settings SHA-256.

The personal top 10 sorts valid comparable runs by average FPS, then 1% low.
History and immutable per-run result JSON files remain below the caller's
explicit local result root. Reusing a `run_id` with different content is
rejected. The store validates result shape, status, metric values, scene order,
benchmark identity and comparison-key consistency before writing. If a process
was interrupted after the immutable run file but before the history update,
recording the identical result again repairs the missing local index entry.
An unsafe invalid input ID is replaced with a deterministic local digest ID so
it cannot escape the configured result directory.

This is a personal local comparison, not tamper-proof competition evidence.
The normalized capture and active-confirmation field can be inspected and
edited by the machine owner. V1 therefore makes no anti-cheat, attestation or
public-leaderboard claim.

## Local desktop screenshot page

The renderer writes one self-contained HTML file with no scripts, external
assets or network links. It displays the current result and the matching local
top 10. It deliberately has no Share, Upload, Discord or Steam button. The
footer states the local-only/no-Optimizer boundary so a user-made screenshot
keeps that context. This V1 page is a desktop result view; no separate mobile
layout or mobile product path is part of the scope.

## CLI

```powershell
iy-benchmark-result .\capture.json .\console.log --root .\results\benchmark --html .\results\benchmark\latest.html
```

The command exits with code `0` only for a valid measurement and `2` for a
recorded invalid result. Generated captures, results, histories and HTML pages
are local artifacts and must not be committed as product evidence.
