# Improve Matrix Pack 01 — Read-only System-Check Basis

## Version and boundary

`config/rule-packs/improve-matrix-pack-01.json` is Pack **1.0.0** in
`iy.improve_rule_pack/v1` format. It is a machine-readable, read-only export
of existing System-Check semantics, not a catalog of performance tweaks.

It contains the twelve existing System-Check bases: Windows, CPU, memory,
mainboard, GPU, GPU-driver currentness, chipset-driver currentness, graphics
settings profile, display, monitor, Secure Boot and TPM. The seven graphics
setting IDs remain distinct data identifiers: `latency`, `upscaling`,
`frame_pacing`, `sync`, `sharpening`, `quality_overrides` and `game_tuning`.

All entries have `apply_capable: false`, `restore_capable: false` and a
`NO_CHANGE` or protected security class. The pack cannot issue a normal
positive Improve recommendation. `SECURITY_PERFORMANCE_TRADEOFF` entries are
explicitly protected by the existing engine and remain read-only.

## Provenance

The source contract is the existing committed System-Check implementation at
`origin/main@2cd358c`, `src/improve_yourself/system_check.py`. It carries only
the already fixed mapping for AMD Radeon RX 7900 XTX, Gigabyte X870 GAMING X
WIFI7 and AMD X870. The three linked manufacturer pages are source locations,
not release-fixed driver values: a live comparison is time-bound and becomes
Unknown/Review if it is unavailable or cannot be compared.

No other hardware receives a guessed chipset, driver currentness, graphics
profile value or optimization recommendation.

## Validation and regression

The existing fail-closed import gate validates every rule before use. The
official Pack-01 corpus runs it through exactly 150 deterministic synthetic
`iy.system_profile/v1` profiles. They model logic coverage only, never real
hardware performance or confidence. The corpus deliberately retains known
facts, missing fields, conditional unsupported mappings and existing fixture
conflict-contract coverage; Pack 01 itself declares no invented conflict.

The checked Pack-01 result is deterministic: 12 rules × 150 profiles produce
1,800 results: `RECOMMENDED: 0`, `ALREADY_RECOMMENDED: 0`, `NO_CHANGE: 1,159`,
`CONDITIONAL: 172`, `INSUFFICIENT_EVIDENCE: 469`. The 90 NVIDIA mappings are
explicitly excluded from the two AMD-only checks. The exact chipset mapping is
conditional for 143 profiles rather than guessed. Missing board data, driver
data, monitor identity and security evidence remain insufficient; the 300
missing Secure-Boot/TPM results remain visible as `INSUFFICIENT_EVIDENCE`.

There are no Pack-01 conflicts because the source System-Check contract
declares none. The pre-existing fixture conflict contract stays in the shared
150-system test corpus and proves the generic deterministic conflict behavior
without inventing a real Pack-01 conflict.

The generic UI contract distinguishes `READ-ONLY FACTS AVAILABLE`,
`CONDITIONAL / NOT CONFIRMED`, `UNSUPPORTED / EXCLUDED` and
`UNKNOWN / NOT AVAILABLE`. It keeps evidence, compatibility traces and missing
paths visible, and it exposes no Apply action. The normal desktop System
Check/Optimizer route loads the bundled Pack 01 through the same fail-closed
importer. If loading fails, it clears the product evaluation and explains that
no optimizer assessment is shown; it never falls back to fixtures.
