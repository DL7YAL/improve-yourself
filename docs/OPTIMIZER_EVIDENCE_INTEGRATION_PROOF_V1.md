# Optimizer Evidence Integration Proof V1

## Proven pipeline

The Foundation now proves one shared, read-only path:

`COLLECT → SYSTEM_PROFILE → RULE_COMPATIBILITY → EVIDENCE → RECOMMENDATION_RESULT → UI_VIEWMODEL`

`integration_proof()` only orchestrates existing Foundation functions; it does
not introduce a second engine. Each result contains the exact rule, domain,
state, rationale, missing evidence, required-condition trace, exclusion trace,
conflicts and the Evidence Records considered.

## Evidence separation

The report keeps two explicit paths:

- configuration evidence: device/configuration observations;
- observed network quality: `OBSERVED_NETWORK_QUALITY` records from Network
  Quality Collector V1.

The observed path carries the declared target and measurement outcome. Its
provenance says that correlation is not configuration causation. It cannot
select an adapter setting or create a network recommendation on its own.

## Fixture proof

Six fixture-only rules demonstrate System, Graphics, Network, BIOS,
conditional/exclusion and `SECURITY_PERFORMANCE_TRADEOFF` paths. They never
become a real Improve recommendation: the UI ViewModel labels every fixture
state `FIXTURE_ONLY — <state>` and sets `apply_available: false`.

The proof covers RECOMMENDED, ALREADY_RECOMMENDED, CONDITIONAL, NO_CHANGE,
INSUFFICIENT_EVIDENCE and explicit exclusion. Missing values always become an
explainable non-positive outcome. Security/performance trade-off fixtures are
always `NO_CHANGE`, regardless of their ordinary compatibility conditions.

The existing 150-system matrix remains synthetic decision coverage only; it
does not contain validation results or real performance evidence.

## UI data contract

For each selected fixture, the ViewModel exposes the fixed Optimizer hierarchy,
domain, title, current state, fixture-marked recommendation, status, setting
explanation, system-specific rationale, possible effect, evidence/validity,
risks, restore/change metadata, BIOS guidance and explainability trace. It
contains no Apply button or write capability.
