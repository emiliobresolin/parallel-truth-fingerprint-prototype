# Instrument profiles v1

`InstrumentProfile.v1` is an immutable, offline description of a bounded
instrument transfer/configuration claim. It is neither device configuration,
proof of possession, wiring, calibration, acquisition, plant behavior, nor
authorization for an experiment or control action. Every profile and every
admission/evaluation result has `authorization_effect: none`.

## Admission boundary

The only route to conversion or evaluation is an `AdmittedInstrumentProfile`
handle produced from one immutable registry snapshot. Admission is a pure,
resolver-injected DAG:

```text
source/use revision -> parameter revisions -> inventory -> required set
                     -> profile revision -> accountable gate + admitted handle
```

Mutable selectors (`latest`, `current`), a hash mismatch, unresolved source
use/locator, an unauditable parameter gate, missing/duplicate transform, or a
role/unit/scope mismatch reject only that candidate. A rejected profile cannot
be converted by supplying its structural payload directly.

## Initial catalog state

The authoritative catalog is
[`instrument-profiles.v1.json`](reference-archive/catalog/instrument-profiles.v1.json).
All four records are retained as independent `unavailable_blocking` planning
candidates:

| Profile | Retained evidence claim | Blocking closure |
| --- | --- | --- |
| TH320 | D73 Pt100, 0-100 degC, four-wire | exact 4-20 mapping/configuration and quality policy |
| P200 | provisional P200, gauge 0-10 bar, two-wire 4-20 mA | archived official option/as-configured bytes; SKU is only a lead |
| FB420 | programmable user-min/user-max RPM relation | RPM endpoints, PPR/geometry, configuration and diagnostics |
| CDS803 | documented 4/20 mA terminal relation and planning-frozen 0/100 decision | terminal 53 current-mode verification and exact upstream closure |

No profile substitutes legacy ranges, manufacturer defaults, a generic NAMUR
rule, or a `1200-4200 rpm` fallback. In particular, 4 mA alone is not an FB420
fault assertion; it may be its configured lower endpoint.

## Pure conversion and evaluation

The complete binding set has exactly three directions:
`current_to_normalized`, `current_to_engineering_or_reference`, and
`engineering_or_reference_to_current`. The profile layer never derives an
inverse or local affine formula: it invokes the exact injected upstream
`affine_map.v1` revision. Inputs and outputs are finite `Decimal` values, with
`Inexact` and `Rounded` trapped; there is no clipping, tolerance, quantization
or binary-float fallback.

For a measurement transmitter, ordered profile rules run before conversion and
return exactly one of `in_range`, `under_range`, `over_range`, `missing`,
`uncertain`, or `fault`. `missing` invariably means `no_numeric_value`.
Overlapping, absent, or unresolved rules yield the explicit coverage diagnostic.

For a command input, conformance is separate: it validates declared current
mode, quantity, unit, direction and scope, then returns only `conformant` or
`blocked` with `convert` or `no_command_value`. It never creates measurement
quality, sensor evidence, a detector modality, or an observation.

## Stable diagnostic families

`IPV1_SCHEMA_VERSION_TOKEN`, `IPV1_MUTABLE_ALIAS`, `IPV1_CONTENT_HASH`,
`IPV1_SOURCE_USE_LOCATOR`, `IPV1_PARAMETER_GATE`, `IPV1_TRANSFORM_BINDING`,
`IPV1_ROLE_QUANTITY_UNIT_DIRECTION`, `IPV1_ENDPOINT_SPAN`,
`IPV1_QUALITY_COVERAGE`, `IPV1_DIAGNOSTIC_UNRESOLVED`, and
`IPV1_AUTHORIZATION_EFFECT` are deterministic families. Consumers use the
family/token, never the prose explanation.

Story 10.2 owns persistent observations; 10.3 owns runtime/emulator paths;
10.4 owns selection and 25/75 or 8/16 experiment factors. This contract does
not write evidence, access a network/device/dataset, sample a clock or
environment, or activate UI/control work.
