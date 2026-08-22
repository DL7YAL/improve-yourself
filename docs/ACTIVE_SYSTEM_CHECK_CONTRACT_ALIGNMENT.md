# Active System Check Contract Alignment Pass

## Scope

This pass aligns the active `dev/v1-foundation` read-only System Check with the
already versioned twelve-check Pack-01 contract. It adds no product rule,
hardware mapping, collector category, recommendation or write capability.

The active collector was an older eight-check projection. The aligned source is
the existing versioned System Check contract from
`origin/main@2cd358c:src/improve_yourself/system_check.py`. Only that collector
and its existing contract tests were adopted; unrelated main-branch services,
documentation and product work were not merged.

## Contract coverage

The active `iy.system_check/v1` output now contains exactly these twelve check
bases, in the existing order:

1. `windows`
2. `cpu`
3. `memory`
4. `motherboard`
5. `gpu`
6. `gpu_driver`
7. `chipset_driver`
8. `graphics_settings_profile`
9. `display`
10. `monitor`
11. `secure_boot`
12. `tpm`

All collection remains local and read-only. Existing exact manufacturer-source
semantics are retained: only the already specified AMD RX 7900 XTX, Gigabyte
X870 GAMING X WIFI7 and AMD X870 source mappings are considered. Unsupported
or unproven hardware remains Unknown/Unsupported; no generic driver or chipset
currency is inferred from a name or version.

## Projection alignment

The twelve-check collector emits display evidence as `active_displays` and
monitor identity separately as `monitor.monitors`. The Home and optimizer
profile projections now consume those contract fields directly. They retain a
read-only compatibility fallback for previously saved v1 scans that used
`refresh_rates_hz`; that fallback does not synthesize a monitor, refresh rate,
CS2 option or driver state.

Consequently, the Pack-01 path remains:

`System Check -> SYSTEM_PROFILE -> compatibility/evidence -> recommendation result -> UI/ViewModel`

Unknown, conditional and insufficient evidence continue to fail closed. The
same generic UI provides facts and reasons but never an Apply action.

## Repeated real-system evidence pass

On 2026-08-22, the locally available explicitly provided tester system was
checked again. The raw report was used only in a temporary local location and
removed after aggregation; no profile values or absolute paths are stored here.

| Assertion | Result |
| --- | --- |
| System Check schema | `iy.system_check/v1` |
| Read-only policy | confirmed |
| Changes applied | `false` |
| Active checks | 12/12 contract bases |
| System Check statuses | 10 `OK`, 1 `REVIEW`, 1 `ACTION_REQUIRED` |
| Pack-01 results | 11 `NO_CHANGE`, 1 `CONDITIONAL` |
| Positive recommendations | 0 |
| Apply available | `false` |

This is one read-only real-system observation, not a hardware golden master,
performance result or release-wide compatibility claim. No extra real tester
system was available in the current workspace; it is therefore not represented
as tested.

## Validation

- Focused System Check, projection, Pack and shell tests: **42 passed**.
- Full test suite: **182 passed**.
- `compileall`: PASS.
- `git diff --check`: PASS before the checkpoint.

## Remaining evidence boundaries

- The three existing manufacturer mappings are deliberately narrow and their
  live source values are not release-fixed.
- Monitor identity, security state, driver and chipset currentness remain
  conditional or insufficient whenever their actual collector evidence is
  unavailable; this is not a negative hardware verdict.
- One local tester validates the path only. Additional explicitly provided
  real tester systems are required before making broader compatibility claims.
- There is still no Apply, Snapshot/Restore, registry, BIOS, driver, network
  or benchmark operation in this path.

## One permitted next step

After an explicit product decision, repeat this same read-only Evidence Pass
for additional explicitly provided tester systems and classify the resulting
Unknown/Conditional/Exclusion cases. Do not broaden hardware support or create
new rules as part of that pass.
