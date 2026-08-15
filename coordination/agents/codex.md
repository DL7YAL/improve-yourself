# Codex

STATUS: done
TASK: Run and validate a representative real-demo Analyzer regression
BRANCH: `dev/v1-foundation`
CHANGED: No product or parser source changed after the harness commit. Ran the prepared regression against one restored representative local demo and updated only the coordination status with aggregate, non-personal evidence. The raw demo, detailed analysis, and generated summary remain under local ignored paths and are not committed.
VERIFIED: End-to-end regression PASS for source SHA-256 `732855381761ad41aaea58dbdb458e8c85cb6e4bccd112f534ad3674f81f00c3`: schema `iy.analysis/v1`, map `de_mirage`, 102 kills, 6 round-wide Multi-Kill markers, quality `limited`, and 2 warnings. Available channels are `bomb`, `damages`, `grenades`, `infernos`, `kills`, `rounds`, `shots`, and `smokes`; `footsteps` is the only missing channel. The validator passed the complete result contract and cross-field invariants. Tickrate is unavailable (`null`) in the current parsed source. The expanded test suite passes `11/11`; both development PowerShell scripts pass AST parsing; `git diff --check` passes.
DECISIONS: Real demos and detailed results remain local and uncommitted. Regression evidence records source SHA-256 and aggregate map/tickrate/count/channel/quality facts, not player names or kill details. Missing `footsteps`/`player_sound` is a disclosed source-capability limitation, not a damaged-demo verdict. Do not commit a real binary fixture unless it is deliberately generated or licensed, non-sensitive, small, and provenance-documented.
OPEN: No blocker remains for this regression work object. The `limited` quality state is expected while the source lacks `footsteps`; tickrate remains unavailable from this parser result and is recorded rather than inferred.
NEXT: Coordination can consume this DONE handoff and select the next FREE implementation object. Preserve the local-only evidence policy if additional demos are compared later.
COMMIT/PR: Regression harness and validator `b01df2f`; this successful real-demo evidence handoff is the next commit on `dev/v1-foundation`.
