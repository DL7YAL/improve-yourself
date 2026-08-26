# Optimizer Real Rule Pack Readiness V1

## Canonical pack contract

`iy.improve_rule_pack/v1` is the fail-closed import contract for a future
curated Improve Matrix Pack. A rule provides stable ID, domain, title, setting,
description, current-state path, candidate state, compatibility requirements
and exclusions, conflicts, evidence records, pack class, risk, restart,
read/apply/restore capabilities, explanations, version and provenance.

Supported pack classes: `RELEASE_CANDIDATE`, `CONDITIONAL`, `EXPERIMENTAL`,
`NO_CHANGE`, `SECURITY_PERFORMANCE_TRADEOFF` and `REJECTED`. Experimental,
rejected and protected trade-off rules cannot become ordinary automatic
recommendations. Apply capability is metadata only; no apply implementation is
enabled by this readiness work.

## Gate and regression

`import_rule_pack()` rejects an entire pack on invalid schema, duplicate ID,
unknown domain/risk/class, missing explanation/state/provenance, invalid or
contradictory compatibility conditions, or absent/incomplete evidence records.
`validate_rule_pack()` then runs the imported rules through the existing
150-profile synthetic matrix with `validate_synthetic_rule_pack()`.

The synthetic regression reports each rule/profile result deterministically.
It cannot create real validation, elevate confidence or produce performance
claims. The imported rules can be passed directly to `optimizer_product_view`
and therefore appear through the existing four domain filters and shared
detail panel with no rule-specific UI implementation.

`fixture_rule_pack_document()` exists solely as a format example and test
fixture. It is marked test-only and does not provide a real rule pack.
