# Optimizer UI Integration V1

## Read-only flow

The existing System Check / Optimizer route now exposes the product flow:

`read-only SYSTEM_PROFILE → shared Foundation → Improve Empfehlungen → domain list → common detail panel`

The top summary reports checked fixture settings, technical matches, already
configured, conditional, insufficient-evidence and manual/BIOS cases. It is
explicit that fixture results are not real Improve recommendations.

## Domain navigation and data-driven contract

The same card/layout family exposes four equal domain filters: System
Optimizer, Graphics Optimizer, Network Optimizer and BIOS Optimizer.

Every rule flows through `optimizer_product_view()` and the existing
`recommendation_detail_view_model()`. No category has its own engine or detail
implementation. Future curated Rule Packs enter through the same contract.

Each card displays name, current state, fixture-marked Improve result, status,
evidence context and manual BIOS marker. The shared details panel contains
explanation, current state, system rationale, potential change,
evidence/validity, risks/trade-offs, restore metadata, BIOS guidance and
compatibility/missing-evidence explainability. It always says no Apply is
available.

Network evidence remains separated in the ViewModel/Foundation as configuration
evidence versus observed network quality. Missing RTT/Jitter/Packet Loss is
shown as missing evidence, never zero.

## Internal test path

`optimizer_product_view(synthetic_profile, internal_test=True)` is a bounded
developer/test path for a selected canonical synthetic profile, such as matrix
profile 037. It is not wired as a normal user action and never changes or
uploads anything.
