# Demo Analyzer V1 — real end-to-end workflow

Date: 2026-08-21
Branch: `dev/v1-foundation`

## Runtime-compatible acceptance proof

The strict CS2 review criterion is closed with the real local demo `fut-vs-mouz-m2-ancient.dem` (SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`, 270,062,278 bytes). The unchanged workflow produced 18 rounds, 10 named players, 235 objective indicators/rule matches and 54 merged scenes. Its first scene generated `demo_gototick 3654`.

The installed CS2 client loaded and normally played the same Ancient demo. After demo readiness, the generated tick command was sent through a localhost-only CS2 netcon connection, visibly returned playback to the first-round combat context, and `demo_togglepause` held the review at 0:58.3 without a parse error. This is runtime evidence for the generated scene tick, not a parser-only claim. No analyzer rule, threshold or evidence boundary was changed for the proof.

The earlier Mirage demo remains useful Awpy evidence but is not the runtime acceptance source because the current CS2 client also fails during its ordinary playback with `Failed to parse message`.

## Implemented flow

```text
.dem
  -> existing Awpy 2.0.2 adapters/builders
  -> iy.analysis/v1 compatibility summary + canonical iy.replay/v2 store
  -> real roster / observed starting line-ups
  -> Full Demo or explicit multi-player selection
  -> neutral review_v1 profile
  -> objective indicators
  -> named rules / combinations
  -> overlapping context merge
  -> analysis-flow JSON + timeline JSON + local review HTML + CS2 tick commands
```

The canonical scene engine consumes replay-v2 identities, round chunks and events. It does not parse the demo independently, create fake events, issue cheat verdicts or fill missing evidence. The compatibility analysis summary and full replay builder currently remain two explicit Awpy passes over the same hash-bound local demo; the scene/rule/review stages consume only the resulting canonical replay truth.

## Selection and roster

- Full Demo analyzes all event participants.
- Player Select accepts one or more stable player IDs and deduplicates them.
- Review UI provides player dropdown, `+ Add Player`, CT, T, Reset and Full Demo.
- Already selected IDs disappear from the dropdown.
- CT/T select the five-player observed starting line-up; they do not create another analysis mode.
- Display names are shown while Steam-based IDs remain internal.

## V1 objective indicators

- kill;
- headshot when Awpy supplies the qualifier;
- wallbang when `penetrated > 0`;
- smoke kill when Awpy supplies through-smoke evidence;
- blind kill when Awpy supplies attacker-blind evidence;
- entry as the first evidenced kill of a round;
- multi-kill as two kills by one attacker within 320 canonical ticks.

Trade remains disabled because the real reference demo has no evidenced tick rate and the current rule does not guess a seconds-based trade window. Information-review rules likewise emit nothing until sight, sound, prior-information and additional context conditions are all defined and evidenced.

Each match receives a deterministic `128`-tick pre-context and `256`-tick post-context. Overlapping or near-adjacent matches in the same round merge with a `96`-tick gap allowance. Marker types, event IDs, players and ticks are unioned into one scene, eliminating duplicate outputs for a kill that is also an entry/headshot/wallbang/etc.

## Real demo evidence

Local source SHA-256: `2d70058ba006fecebf804e499a13ebeab97308804b433723c0657bf7810927a2`

- parser: Awpy `2.0.2`;
- map: `de_mirage`;
- rounds: `30`;
- real named players: `10`;
- observed starting line-ups: `5 CT`, `5 T`;
- kills: `201`;
- headshots: `98`;
- entries: `30`;
- through-smoke kills: `21`;
- wallbangs: `6`;
- bounded multi-kill combinations: `19`;
- objective rule matches/markers: `375`;
- merged situations/scenes: `97`;
- explicit one-player run: `35` scenes;
- first review tick: `6352`;
- generated local command: `demo_gototick 6352`.

Generated results are ignored/local. No demo, player-detail result, HTML or timeline is committed.

## Validation and remaining runtime gate

- automated suite: `97 passed`;
- seven public CLI help-smokes: PASS;
- real `.dem -> Awpy -> teams/players -> selection -> events -> merged scenes -> timeline/JSON/HTML`: PASS;
- source/map/parser identity and first tick command: PASS;
- `git diff --check`: PASS before checkpoint;
- actual CS2 jump to tick `6352`: NOT YET VERIFIED.

CS2 was started and reached its main menu. The UI controller then detected active user input while opening settings, so automation stopped immediately and sent no further keys/clicks. Completion requires an idle CS2 window, loading the same local demo, applying the generated tick command, and visually confirming that playback lands at the intended scene. No repository change is needed for that final gate unless CS2 rejects the generated command.
