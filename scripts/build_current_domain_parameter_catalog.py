"""Build the accountable current-domain parameter catalog.

The legacy planning catalog deliberately carries unresolved engineering-unit
profiles.  It must not be repurposed as a runtime gate.  This builder produces
the narrow execution catalog used by the current-domain path: the archived
FB420 documentation's directly proportional 4--20 mA output only.

Engineering values (RPM, bar, and degrees Celsius) may be displayed as
annotated context, but are not inputs to a current-domain calculation unless a
separate, exact instrument configuration is later admitted.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from parallel_truth_fingerprint.contracts.parameter_evidence import (
    CategoryDisposition,
    CategoryState,
    InventoryCategory,
    NumericConsumerInventory,
    ParameterBinding,
    ParameterEvidenceCatalog,
    ParameterRequirement,
    RequiredParameterSet,
)
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    canonical_parameter_catalog_bytes,
    load_parameter_catalog,
    parameter_catalog_identity,
    source_catalog_identity,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog


DEFAULT_SOURCE = ROOT / "docs/reference-archive/catalog/source-catalog.v1.json"
DEFAULT_LEGACY = ROOT / "docs/reference-archive/catalog/parameter-evidence.v1.json"
DEFAULT_OUTPUT = ROOT / "docs/reference-archive/catalog/parameter-evidence-current-domain.v1.json"


def build(*, source_path: Path = DEFAULT_SOURCE, legacy_path: Path = DEFAULT_LEGACY) -> ParameterEvidenceCatalog:
    """Construct the immutable, single-purpose 4--20 mA gate catalog."""

    source_catalog = load_source_catalog(source_path.read_bytes())
    legacy_catalog = load_parameter_catalog(legacy_path.read_bytes())
    current_range = next(
        item for item in legacy_catalog.parameter_revisions
        if item.parameter_id == "rpm.output_signal"
    )
    requirement = ParameterRequirement(
        slot_id="slot:signal.loop_current.range",
        category=InventoryCategory.RANGES_ENDPOINTS,
        consumer_locator=current_range.consumer_locator,
        quantity_kind=current_range.quantity_kind,
        unit=current_range.unit,
        value_role=current_range.value_role,
        scope=current_range.experiment_scope,
        profile_id=current_range.profile_id,
        not_applicable_allowed=False,
    )
    dispositions = tuple(
        CategoryDisposition(
            category=category,
            state=(CategoryState.REQUIRED if category == InventoryCategory.RANGES_ENDPOINTS
                   else CategoryState.NOT_APPLICABLE),
            rationale=(
                "The execution calculation consumes the archived FB420 4-20 mA interval."
                if category == InventoryCategory.RANGES_ENDPOINTS else
                "This current-domain gate has no consumer in this category."
            ),
            owner_approved=True,
        )
        for category in InventoryCategory
    )
    inventory = NumericConsumerInventory(
        inventory_id="numeric-consumer-inventory:current-domain-4-20ma-v1",
        component_identity="current-domain:signal-observation-runtime",
        contract_identity="SignalObservation.v2 raw-current primary representation",
        code_identity="sha256:current-domain-runtime-no-engineering-inputs-v1",
        scope=current_range.experiment_scope,
        profile_id=current_range.profile_id,
        requirements=(requirement,),
        category_dispositions=dispositions,
    )
    required = RequiredParameterSet(
        required_set_id="required-parameter-set:current-domain-4-20ma-v1",
        catalog_identity="",
        source_catalog_identity=source_catalog_identity(source_catalog),
        vocabulary_version=legacy_catalog.semantic_vocabulary_version,
        inventory_id=inventory.inventory_id,
        scope=inventory.scope,
        profile_id=inventory.profile_id,
        experiment_id="current-domain:runtime-input-gate-v1",
        component_identity=inventory.component_identity,
        bindings=(ParameterBinding(
            slot_id=requirement.slot_id,
            parameter_revision_id=current_range.parameter_revision_id,
            parameter_revision_sha256=current_range.revision_sha256,
            not_applicable=False,
            rationale="Archived FB420 source directly establishes the bounded 4-20 mA output.",
        ),),
    )
    catalog = ParameterEvidenceCatalog(
        schema_version=legacy_catalog.schema_version,
        semantic_vocabulary_version=legacy_catalog.semantic_vocabulary_version,
        source_catalog_identity=source_catalog_identity(source_catalog),
        parameter_revisions=(current_range,),
        derivations=(),
        decisions=(),
        mock_admissions=(),
        measurements=(),
        inventories=(inventory,),
        required_sets=(required,),
        locus_audits=(),
        legacy_quarantine=(),
    )
    return replace(
        catalog,
        required_sets=(replace(required, catalog_identity=parameter_catalog_identity(catalog)),),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_bytes(canonical_parameter_catalog_bytes(build()))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
