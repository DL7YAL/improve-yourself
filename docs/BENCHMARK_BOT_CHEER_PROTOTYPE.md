# Benchmark cinema audience — one-bot cheer prototype gate

Status: **PROTOTYPE REQUIRED — NOT IMPLEMENTED**

Runtime authority: the Windows benchmark machine with the installed CS2
Workshop Tools build. Linux/WSL is only the SSH/Git connection and cannot close
this in-engine gate.

## Established state

- Candidate 2 creates five T and five CT bots, stops their AI and stages them
  deterministically for each measured scene.
- During the three-second boot delay, those ten bots use fixed cinema spawn
  positions facing the screen. The VMAP contains 32 fixed team spawn slots,
  but no additional active bots are created for presentation.
- The installed `point_script.d.ts` exposes player lookup, teleport, health,
  armor, weapons and inherited model operations for `CSPlayerPawn`. It exposes
  no player animation, activity, sequence or gesture method.
- Installed Hammer FGD inputs such as `SetAnimationLooping` belong to dynamic
  props, not to `CSPlayerPawn`.
- A read-only lookup in the installed `pak01_dir.vpk` directory index confirms
  Valve runtime resources for end-of-match UI celebration clips and cheer
  voice lines. No payload was extracted or copied. Their presence does not
  prove that the clips can drive live gameplay pawns.

## Rejected assumptions

- Do not send prop-only animation inputs to every live player and call the
  absence of a script exception proof of animation success.
- Do not treat `CW.Cheer`, radio audio or weapon inspect as a visible cheering
  animation without an in-game visual result.
- Do not replace the bots silently with animated character props. That would
  be a presentation proxy, not proof that the existing bots cheer.
- Do not reference or copy celebration clip payloads into the repository.
- Do not change candidate version, controller hash or measured workload before
  a one-bot prototype visibly succeeds.

## Required Windows prototype

Use a disposable local copy of the addon/map and one existing bot only:

1. Record the authoritative VMAP/controller hashes and create a target-limited
   backup before editing.
2. Keep nine bots unchanged. Select one cinema bot as the prototype target.
3. Test one mechanism at a time, beginning with documented gameplay behavior.
   Record the exact command/input, selected bot model, animation identifier,
   console output and a short local capture.
4. A mechanism passes only when the bot remains at its fixed floor position,
   faces the screen, visibly performs a standing cheer, produces no script,
   animation, nav or AI error, and repeats identically after two clean map
   restarts.
5. Restore the disposable addon copy after each failed mechanism. Do not
   deploy a failed probe to the authoritative addon.

If no documented live-pawn mechanism passes, keep the result
`INSUFFICIENT_EVIDENCE`. A visible prop-based audience may be proposed as a
separate design decision, but requires explicit owner approval because it
changes the meaning of “bots as audience.”

## Evidence record

For a successful probe record only safe metadata in Git:

- mechanism and exact deterministic phase schedule;
- CS2/Workshop Tools build identity;
- prototype bot team/model and fixed transform;
- two restart results;
- console result and local capture SHA-256 values;
- workload behavior during boot delay, warmup and measured pass;
- restore/deploy verification and final source hashes.

Raw captures, logs, Valve payloads and private absolute paths remain local.
