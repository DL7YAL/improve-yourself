# CS2 review coordinator V1

Date: 2026-08-21  
Branch: `dev/v1-foundation`

## Purpose

The coordinator connects one already generated scene to installed CS2 without becoming another replay or process authority. A review button sends a scene ID and tick to a loopback-only endpoint. Browser input is never trusted as scene truth.

## Fail-closed flow

```text
review scene button
  -> same-origin POST on 127.0.0.1
  -> request size and JSON validation
  -> exact scene ID/tick lookup in analysis-flow.json
  -> local CS2 netcon readiness probe
  -> status must report Client: Connected [DEMO]
  -> demo_info filename must equal workflow source_demo_name
  -> send the generated demo_gototick only
  -> return visible sent/error status
```

The server never binds externally. Foreign origins, unknown scenes, altered ticks, missing demo mode, missing identity and wrong filenames fail without sending a tick. `status` and `demo_info` are read-only probes; `demo_gototick` is the only state-changing CS2 command.

## Real evidence

Installed CS2 on localhost netcon reported:

```text
Client:  Connected [DEMO]
Demo contents for iy_ancient.dem:
```

The real canonical Ancient flow allowed `r1-t3654-0` only at tick `3654`. The coordinator accepted that exact pair and active filename, sent the tick, and CS2 visibly returned to approximately 0:57 in the first-round context. No parser, rule, scene or timeline data was recomputed.

## Boundary

The coordinator does not launch or restart CS2, set Steam launch options, add a netcon port, copy or rename demos, pause playback or decide which scene is relevant. A renamed runtime copy is deliberately rejected because the source identity cannot be proven equivalent from CS2's filename evidence alone.

## Desktop readiness preflight

Before review, the shell displays three independent evidence states:

1. local netcon reachable;
2. CS2 reports active `[DEMO]` playback;
3. `demo_info` filename exactly matches the workflow source basename.

`Review öffnen` remains disabled until all states pass. A Review click repeats the probe asynchronously, so an earlier green result cannot become a stale authorization after CS2 or the active demo changes. Import and selection changes reset the displayed state. The panel explains a missing local connection, inactive demo, missing filename or exact mismatch but performs no corrective system or CS2 action.

Live evidence separated the identity boundary correctly: expected/active `iy_ancient.dem` returned ready, while expected `fut-vs-mouz-m2-ancient.dem` with active `iy_ancient.dem` returned a filename mismatch despite both files being related in the manual test setup.
