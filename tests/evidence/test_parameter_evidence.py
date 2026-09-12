from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from parallel_truth_fingerprint.contracts.parameter_evidence import (
    PARAMETER_EVIDENCE_SCHEMA_VERSION,
    AccountabilityOutcome,
    ApprovalState,
    AuthenticFeasibility,
    CategoryDisposition,
    CategoryState,
    ConformanceVector,
    DecisionAuthority,
    DecisionRecord,
    DecisionValue,
    DerivationKind,
    DerivationSpec,
    DerivedAuthority,
    DirectAuthority,
    InventoryCategory,
    MeasurementEvidenceRef,
    MeasuredAuthority,
    MockAdmission,
    MockAuthority,
    MockParameterRevisionBinding,
    MockSupportClaim,
    NumericConsumerInventory,
    NumericLocus,
    NumericLocusAudit,
    NumericValue,
    NumericValueKind,
    ParameterBinding,
    ParameterClass,
    ParameterEvidenceCatalog,
    ParameterGateResult,
    ParameterRequirement,
    ParameterRevision,
    QuantityKind,
    RandomnessMode,
    RecordState,
    ReproductionDisposition,
    RequiredParameterSet,
    TemporalGateContext,
    UncertaintyKind,
    UncertaintyRecord,
    Unit,
    ValueRole,
)
from parallel_truth_fingerprint.evidence.parameter_evidence import (
    canonical_parameter_catalog_bytes,
    load_parameter_catalog,
    decision_record_identity,
    mock_admission_identity,
    parameter_catalog_identity,
    parameter_revision_identity,
    source_catalog_identity,
    validate_parameter_gate,
)
from parallel_truth_fingerprint.evidence.source_catalog import load_source_catalog


class ParameterEvidenceTest(unittest.TestCase):
    CATALOG_PATH = Path("docs/reference-archive/catalog/parameter-evidence.v1.json")
    SOURCE_PATH = Path("docs/reference-archive/catalog/source-catalog.v1.json")

    def _machine(self) -> tuple[ParameterEvidenceCatalog, object]:
        return (load_parameter_catalog(self.CATALOG_PATH.read_bytes()),
                load_source_catalog(self.SOURCE_PATH.read_bytes()))

    def _na(self, rationale: str = "Synthetic exact-value fixture.") -> UncertaintyRecord:
        return UncertaintyRecord(UncertaintyKind.NOT_APPLICABLE, None, None, None, (), None, None,
                                 rationale)

    def _gate(
        self,
        target: ParameterRevision,
        source_catalog: object,
        *,
        other_parameters: tuple[ParameterRevision, ...] = (),
        derivations: tuple[DerivationSpec, ...] = (),
        decisions: tuple[DecisionRecord, ...] = (),
        mocks: tuple[MockAdmission, ...] = (),
        measurements: tuple[MeasurementEvidenceRef, ...] = (),
        evidence_root: Path | None = None,
        resolver: object = None,
        context: TemporalGateContext | None = None,
    ) -> tuple[ParameterEvidenceCatalog, ParameterGateResult]:
        requirement = ParameterRequirement(
            slot_id="slot:target", category=InventoryCategory.RANGES_ENDPOINTS,
            consumer_locator=target.consumer_locator, quantity_kind=target.quantity_kind,
            unit=target.unit, value_role=target.value_role, scope=target.experiment_scope,
            profile_id=target.profile_id, not_applicable_allowed=False,
        )
        dispositions = tuple(CategoryDisposition(
            category=item,
            state=(CategoryState.REQUIRED if item == InventoryCategory.RANGES_ENDPOINTS
                   else CategoryState.NOT_APPLICABLE),
            rationale="Synthetic complete inventory disposition.", owner_approved=True,
        ) for item in InventoryCategory)
        inventory = NumericConsumerInventory(
            inventory_id="inventory:synthetic", component_identity="component:synthetic",
            contract_identity="contract:synthetic", code_identity="sha256:" + "1" * 64,
            scope=target.experiment_scope, profile_id=target.profile_id,
            requirements=(requirement,), category_dispositions=dispositions,
        )
        source_identity = source_catalog_identity(source_catalog)  # type: ignore[arg-type]
        required = RequiredParameterSet(
            required_set_id="required:synthetic", catalog_identity="",
            source_catalog_identity=source_identity, vocabulary_version="semantic-vocabulary.v1",
            inventory_id=inventory.inventory_id, scope=inventory.scope, profile_id=inventory.profile_id,
            experiment_id="experiment:synthetic", component_identity=inventory.component_identity,
            bindings=(ParameterBinding(
                "slot:target", target.parameter_revision_id, target.revision_sha256, False,
                "Exact synthetic binding.",
            ),),
        )
        catalog = ParameterEvidenceCatalog(
            schema_version=PARAMETER_EVIDENCE_SCHEMA_VERSION,
            semantic_vocabulary_version="semantic-vocabulary.v1",
            source_catalog_identity=source_identity,
            parameter_revisions=other_parameters + (target,), derivations=derivations,
            decisions=decisions, mock_admissions=mocks, measurements=measurements,
            inventories=(inventory,), required_sets=(required,), locus_audits=(), legacy_quarantine=(),
        )
        required = replace(required, catalog_identity=parameter_catalog_identity(catalog))
        catalog = replace(catalog, required_sets=(required,))
        result = validate_parameter_gate(
            catalog, source_catalog, inventory, required, evidence_root=evidence_root,
            path_resolver=resolver, temporal_context=context,  # type: ignore[arg-type]
        )
        return catalog, result

    def _direct_scalar(
        self, parameter_id: str, value: str, unit: Unit, quantity: QuantityKind,
        source_catalog: object,
    ) -> ParameterRevision:
        expected_use = ("use:vendor-danfoss-cds803-programming-2021:83793a7bb3f6de8f"
                        if value == "20" and unit == Unit.MILLIAMPERE
                        else "use:vendor-danfoss-cds803-programming-2021:58f68d1f90e51c14")
        use = next(item for item in source_catalog.uses  # type: ignore[attr-defined]
                   if item.use_id == expected_use)
        numeric = NumericValue(NumericValueKind.SCALAR, scalar=value)
        record = ParameterRevision(
            parameter_id=parameter_id, parameter_revision_id=f"revision:{parameter_id}",
            revision_sha256="",
            parameter_class=ParameterClass.DIRECT, value_role=ValueRole.SINGLE,
            value=numeric, unit=unit, quantity_kind=quantity, record_state=RecordState.VALID,
            approval_state=ApprovalState.APPROVED, migration_status="synthetic_valid_fixture",
            profile_id="profile:synthetic", experiment_scope="scope:synthetic",
            authentic_reproduction_feasibility=AuthenticFeasibility.AVAILABLE,
            prototype_component=use.prototype_component, consumer_locator=f"consumer:{parameter_id}",
            research_question=use.research_question, evidence_track=use.evidence_track,
            final_package_element=use.final_package_element,
            transferability_rationale=use.transferability_rationale,
            limitations=("Synthetic unit-test fixture only.",), uncertainty=self._na(), owner="Emilio",
            synthetic_status="authentic",
            direct_authority=DirectAuthority(
                use.source_revision_id, use.use_id, numeric, unit, quantity
            ),
        )
        return replace(record, revision_sha256=parameter_revision_identity(record))

    def _decide(
        self, records: tuple[ParameterRevision, ...], source_catalog: object,
    ) -> tuple[tuple[ParameterRevision, ...], DecisionRecord, TemporalGateContext]:
        decided = tuple(
            replace(candidate, revision_sha256=parameter_revision_identity(candidate))
            for candidate in (
                replace(item, parameter_class=ParameterClass.PREREGISTERED_FACTOR,
                        direct_authority=None, decision_authority=DecisionAuthority("decision:fixture"),
                        revision_sha256="")
                for item in records
            )
        )
        capability = next(item for item in source_catalog.uses  # type: ignore[attr-defined]
                          if str(item.claim_use) == "capability" and str(item.status) == "located")
        first = decided[0]
        decision = DecisionRecord(
            "decision:fixture", "", "sha256:" + "6" * 64, "Emilio", "Emilio",
            "2026-08-19T10:00:00-03:00", "2026-08-19T10:00:00-03:00", False,
            True, True, tuple(item.parameter_id for item in decided),
            tuple(DecisionValue(item.parameter_id, item.value, item.unit, item.quantity_kind,
                                item.value_role) for item in decided),
            first.profile_id, first.experiment_scope, first.prototype_component,
            first.research_question, first.evidence_track, first.final_package_element,
            "Synthetic bounded arithmetic fixture.", (capability.use_id,),
            ("manufacturer recommendation",), ("Unit test only.",),
        )
        decision = replace(decision, record_sha256=decision_record_identity(decision))
        context = TemporalGateContext(
            "context:fixture", decision.record_sha256, decision.freeze_time,
            "sha256:" + "7" * 64, "2026-08-20T10:00:00-03:00",
            "sha256:" + "8" * 64, "2026-08-21T10:00:00-03:00",
        )
        return decided, decision, context

    def test_contract_tokens_are_closed_and_authorization_is_none(self) -> None:
        self.assertEqual(PARAMETER_EVIDENCE_SCHEMA_VERSION, "parameter-evidence.v1")
        self.assertEqual({item.value for item in ParameterClass},
                         {"direct", "derived", "measured", "preregistered_factor", "mock"})
        result = ParameterGateResult(
            gate_result_id="sha256:" + "a" * 64,
            catalog_identity="sha256:" + "b" * 64,
            source_catalog_identity="sha256:" + "c" * 64,
            vocabulary_version="semantic-vocabulary.v1",
            inventory_id="inventory:test",
            required_set_id="required:test",
            temporal_context_id=None,
            decision_ids=(),
            measurement_evidence_ids=(),
            mock_admission_ids=(),
            validator_identity="sha256:" + "d" * 64,
            accountability_outcome=AccountabilityOutcome.BLOCKED,
            violations=(), limitations=("Synthetic test.",),
        )
        self.assertEqual(result.authorization_effect, "none")
        with self.assertRaises(TypeError):
            ParameterGateResult(**{**result.__dict__, "authorization_effect": "authorize"})

    def test_migrated_machine_authority_is_deterministic_and_honestly_blocked(self) -> None:
        catalog, source_catalog = self._machine()
        self.assertEqual(len(catalog.parameter_revisions), 15)
        self.assertEqual(len(catalog.legacy_quarantine), 20)
        self.assertEqual(len(catalog.locus_audits[0].entries), 28)
        self.assertTrue({"tool-python-314-decimal", "std-bipm-si-brochure-9-v4.01-2026"}.issubset(
            {item.source_id for item in source_catalog.sources}  # type: ignore[attr-defined]
        ))
        self.assertTrue({
            "use:std-jcgm-100-2008:introduction-0.1",
            "use:std-jcgm-100-2008:introduction-0.7-item-1",
            "use:std-jcgm-100-2008:definition-2.2.3",
        }.issubset({item.use_id for item in source_catalog.uses}))  # type: ignore[attr-defined]
        self.assertEqual(self.CATALOG_PATH.read_bytes(), canonical_parameter_catalog_bytes(catalog))
        self.assertEqual(catalog.required_sets[0].catalog_identity, parameter_catalog_identity(catalog))
        result = validate_parameter_gate(catalog, source_catalog, catalog.inventories[0],
                                         catalog.required_sets[0])
        self.assertEqual(result.accountability_outcome, AccountabilityOutcome.BLOCKED)
        self.assertEqual(result.authorization_effect, "none")
        self.assertTrue({"PAR-INVENTORY-INCOMPLETE", "PAR-SOURCE-INELIGIBLE",
                         "PAR-DERIVATION-INVALID", "PAR-DECISION-INVALID"}.issubset(
                             {item.rule_id for item in result.violations}
                         ))

    def test_valid_direct_parameter_can_be_accountable(self) -> None:
        machine, source_catalog = self._machine()
        target = next(item for item in machine.parameter_revisions
                      if item.parameter_id == "command.terminal53.low_current")
        _, result = self._gate(target, source_catalog)
        self.assertEqual(result.accountability_outcome, AccountabilityOutcome.ACCOUNTABLE,
                         [item.to_dict() for item in result.violations])
        tampered = replace(target, transferability_rationale="Tampered after revision freeze.")
        self.assertIn("PAR-REVISION-HASH-MISMATCH", {
            item.rule_id for item in self._gate(tampered, source_catalog)[1].violations
        })

    def test_decimal_and_interval_forms_fail_closed(self) -> None:
        _, source_catalog = self._machine()
        base = self._direct_scalar("decimal", "1", Unit.ONE, QuantityKind.DYNAMIC_FACTOR,
                                   source_catalog)
        for invalid in (" 1", "1.0", "1_0", "1e0", "NaN", "Infinity", "-0", "١"):
            with self.subTest(invalid=invalid):
                target = replace(base, value=NumericValue(NumericValueKind.SCALAR, scalar=invalid),
                                 direct_authority=replace(base.direct_authority,
                                                          documented_value=NumericValue(
                                                              NumericValueKind.SCALAR, scalar=invalid)))
                _, result = self._gate(target, source_catalog)
                self.assertIn("PAR-DECIMAL-INVALID", {item.rule_id for item in result.violations})
        interval = replace(base, value=NumericValue(
            NumericValueKind.INTERVAL, lower="2", upper="1", lower_inclusive=True,
            upper_inclusive=True), direct_authority=replace(
                base.direct_authority, documented_value=NumericValue(
                    NumericValueKind.INTERVAL, lower="2", upper="1", lower_inclusive=True,
                    upper_inclusive=True)))
        self.assertIn("PAR-DECIMAL-INVALID",
                      {item.rule_id for item in self._gate(interval, source_catalog)[1].violations})

    def test_authority_class_relabelling_and_quantity_transfer_fail(self) -> None:
        _, source_catalog = self._machine()
        base = self._direct_scalar("authority", "4", Unit.MILLIAMPERE,
                                   QuantityKind.LOOP_CURRENT, source_catalog)
        relabelled = replace(base, parameter_class=ParameterClass.MOCK)
        wrong_quantity = replace(base, quantity_kind=QuantityKind.PRESSURE_ABSOLUTE)
        self.assertIn("PAR-AUTHORITY-MISMATCH",
                      {item.rule_id for item in self._gate(relabelled, source_catalog)[1].violations})
        self.assertIn("PAR-SOURCE-INELIGIBLE",
                      {item.rule_id for item in self._gate(wrong_quantity, source_catalog)[1].violations})
        project_choice = self._direct_scalar("project.choice", "25", Unit.PERCENT,
                                             QuantityKind.SPEED_REFERENCE, source_catalog)
        self.assertIn("PAR-SOURCE-INELIGIBLE", {
            item.rule_id for item in self._gate(project_choice, source_catalog)[1].violations
        })
        machine, _ = self._machine()
        p200 = next(item for item in machine.parameter_revisions
                    if item.parameter_id == "instrument.pressure.range")
        p200_as_absolute = replace(
            p200, record_state=RecordState.VALID, approval_state=ApprovalState.APPROVED,
            quantity_kind=QuantityKind.PRESSURE_ABSOLUTE,
            direct_authority=replace(p200.direct_authority,
                                     documented_quantity_kind=QuantityKind.PRESSURE_ABSOLUTE),
        )
        self.assertIn("PAR-SOURCE-INELIGIBLE", {
            item.rule_id for item in self._gate(p200_as_absolute, source_catalog)[1].violations
        })

    def test_constant_and_transform_derivations_are_reproduced_exactly(self) -> None:
        _, source_catalog = self._machine()
        x0 = self._direct_scalar("x0", "0", Unit.PERCENT, QuantityKind.SPEED_REFERENCE,
                                 source_catalog)
        x1 = self._direct_scalar("x1", "100", Unit.PERCENT, QuantityKind.SPEED_REFERENCE,
                                 source_catalog)
        y0 = self._direct_scalar("y0", "4", Unit.MILLIAMPERE, QuantityKind.LOOP_CURRENT,
                                 source_catalog)
        y1 = self._direct_scalar("y1", "20", Unit.MILLIAMPERE, QuantityKind.LOOP_CURRENT,
                                 source_catalog)
        selected = self._direct_scalar("selected", "25", Unit.PERCENT,
                                       QuantityKind.SPEED_REFERENCE, source_catalog)
        (x0, x1, selected), decision, context = self._decide((x0, x1, selected), source_catalog)
        template = self._direct_scalar("derived", "8", Unit.MILLIAMPERE,
                                       QuantityKind.LOOP_CURRENT, source_catalog)
        spec = DerivationSpec(
            "derivation:test", DerivationKind.CONSTANT_RESULT, "affine_map.v1",
            x0.parameter_revision_id, x1.parameter_revision_id, y0.parameter_revision_id,
            y1.parameter_revision_id, selected.parameter_revision_id, None, None, "8",
            Unit.MILLIAMPERE, (), 50, "ROUND_HALF_EVEN",
        )
        target = replace(template, parameter_class=ParameterClass.DERIVED,
                         direct_authority=None, derived_authority=DerivedAuthority(spec.derivation_id),
                         revision_sha256="")
        target = replace(target, revision_sha256=parameter_revision_identity(target))
        _, result = self._gate(target, source_catalog,
                               other_parameters=(x0, x1, y0, y1, selected), derivations=(spec,),
                               decisions=(decision,), context=context)
        self.assertEqual(result.accountability_outcome, AccountabilityOutcome.ACCOUNTABLE,
                         [item.to_dict() for item in result.violations])
        wrong_quantity = replace(target, quantity_kind=QuantityKind.CALIBRATION_PARAMETER)
        self.assertIn("PAR-UNIT-INVALID", {
            item.rule_id for item in self._gate(
                wrong_quantity, source_catalog,
                other_parameters=(x0, x1, y0, y1, selected), derivations=(spec,),
                decisions=(decision,), context=context,
            )[1].violations
        })

        transform_spec = replace(
            spec, derivation_id="derivation:transform",
            derivation_kind=DerivationKind.OBSERVATION_TRANSFORM,
            selected_input_revision_id=None, observation_variable="reference_pct",
            observation_unit=Unit.PERCENT, declared_output=None,
            conformance_vectors=(ConformanceVector("0", "4"), ConformanceVector("50", "12"),
                                 ConformanceVector("100", "20")),
        )
        transform = replace(
            target, parameter_id="transform", parameter_revision_id="revision:transform",
            value=NumericValue(NumericValueKind.OBSERVATION_TRANSFORM),
            consumer_locator="consumer:transform",
            derived_authority=DerivedAuthority(transform_spec.derivation_id), revision_sha256="",
        )
        transform = replace(transform, revision_sha256=parameter_revision_identity(transform))
        _, result = self._gate(transform, source_catalog,
                               other_parameters=(x0, x1, y0, y1, selected), derivations=(transform_spec,),
                               decisions=(decision,), context=context)
        self.assertEqual(result.accountability_outcome, AccountabilityOutcome.ACCOUNTABLE,
                         [item.to_dict() for item in result.violations])
        duplicate_vectors = replace(
            transform_spec,
            conformance_vectors=(ConformanceVector("0", "4"),) * 3,
        )
        self.assertIn("PAR-DERIVATION-INVALID", {
            item.rule_id for item in self._gate(
                transform, source_catalog, other_parameters=(x0, x1, y0, y1, selected),
                derivations=(duplicate_vectors,), decisions=(decision,), context=context,
            )[1].violations
        })

    def test_derivations_fail_on_zero_span_cycle_rounding_and_mismatch(self) -> None:
        _, source_catalog = self._machine()
        x0 = self._direct_scalar("dx0", "0", Unit.ONE, QuantityKind.NORMALIZED_SPAN,
                                 source_catalog)
        x1 = self._direct_scalar("dx1", "3", Unit.ONE, QuantityKind.NORMALIZED_SPAN,
                                 source_catalog)
        y0 = self._direct_scalar("dy0", "0", Unit.ONE, QuantityKind.NORMALIZED_SPAN,
                                 source_catalog)
        y1 = self._direct_scalar("dy1", "1", Unit.ONE, QuantityKind.NORMALIZED_SPAN,
                                 source_catalog)
        selected = self._direct_scalar("dselected", "1", Unit.ONE,
                                       QuantityKind.NORMALIZED_SPAN, source_catalog)
        (x0, x1, y0, y1, selected), decision, context = self._decide(
            (x0, x1, y0, y1, selected), source_catalog
        )
        template = self._direct_scalar("dtarget", "1", Unit.ONE,
                                       QuantityKind.NORMALIZED_SPAN, source_catalog)
        base_spec = DerivationSpec(
            "derivation:bad", DerivationKind.CONSTANT_RESULT, "affine_map.v1",
            x0.parameter_revision_id, x1.parameter_revision_id, y0.parameter_revision_id,
            y1.parameter_revision_id, selected.parameter_revision_id, None, None, "1",
            Unit.ONE, (), 50, "ROUND_HALF_EVEN",
        )
        target = replace(template, parameter_class=ParameterClass.DERIVED,
                         direct_authority=None, derived_authority=DerivedAuthority(base_spec.derivation_id))
        cases = {
            "precision_loss": base_spec,
            "zero_span": replace(base_spec, input_high_revision_id=x0.parameter_revision_id),
            "wrong_output": replace(base_spec, declared_output="0"),
            "rounding": replace(base_spec, rounding="ROUND_DOWN"),
        }
        for name, spec in cases.items():
            with self.subTest(name=name):
                _, result = self._gate(target, source_catalog,
                                       other_parameters=(x0, x1, y0, y1, selected),
                                       derivations=(spec,), decisions=(decision,), context=context)
                self.assertIn("PAR-DERIVATION-INVALID", {v.rule_id for v in result.violations})
        cyclic_spec = replace(base_spec, input_low_revision_id=target.parameter_revision_id)
        _, cyclic = self._gate(target, source_catalog,
                               other_parameters=(x0, x1, y0, y1, selected),
                               derivations=(cyclic_spec,), decisions=(decision,), context=context)
        self.assertTrue(any(item.rule_id == "PAR-DERIVATION-INVALID"
                            and "acyclic" in item.explanation for item in cyclic.violations))
        mock_input = replace(x0, synthetic_status="mock_derived")
        _, promoted = self._gate(target, source_catalog,
                                 other_parameters=(mock_input, x1, y0, y1, selected),
                                 derivations=(base_spec,), decisions=(decision,), context=context)
        self.assertIn("PAR-LINEAGE-PROMOTION", {item.rule_id for item in promoted.violations})

    def test_measured_authority_checks_opaque_bytes_scope_and_path_safety(self) -> None:
        _, source_catalog = self._machine()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"opaque calibration evidence\x00"
            (root / "pilot.bin").write_bytes(payload)
            uncertainty = UncertaintyRecord(
                UncertaintyKind.UNCERTAINTY, "0.1", Unit.DEG_C, "method:v1",
                ("component:repeatability",), "k=1", "pilot.bin", None,
            )
            evidence = MeasurementEvidenceRef(
                "measurement:test", "measurement-evidence.v1", "pilot.bin",
                "sha256:" + hashlib.sha256(payload).hexdigest(), len(payload), "method:v1",
                "environment:test", "profile:synthetic", "scope:synthetic",
                ("sample:1",), ("run:1",),
                "2026-08-20T10:00:00-03:00", "48", Unit.DEG_C, uncertainty, "Emilio",
                ApprovalState.APPROVED, ("Only this synthetic environment.",),
            )
            base = self._direct_scalar("measured", "48", Unit.DEG_C,
                                       QuantityKind.TEMPERATURE, source_catalog)
            target = replace(
                base, parameter_class=ParameterClass.MEASURED, direct_authority=None,
                measured_authority=MeasuredAuthority(evidence.measurement_evidence_id),
                uncertainty=uncertainty, revision_sha256="",
            )
            target = replace(target, revision_sha256=parameter_revision_identity(target))
            _, result = self._gate(target, source_catalog, measurements=(evidence,),
                                   evidence_root=root)
            self.assertEqual(result.accountability_outcome, AccountabilityOutcome.ACCOUNTABLE,
                             [item.to_dict() for item in result.violations])
            mismatched_uncertainty = replace(
                evidence, uncertainty=replace(uncertainty, unit=Unit.BAR)
            )
            self.assertIn("PAR-MEASUREMENT-INVALID", {
                item.rule_id for item in self._gate(
                    target, source_catalog, measurements=(mismatched_uncertainty,),
                    evidence_root=root,
                )[1].violations
            })
            for locator in ("../pilot.bin", str((root / "pilot.bin").resolve()), ""):
                with self.subTest(locator=locator):
                    bad = replace(evidence, locator=locator)
                    _, result = self._gate(target, source_catalog, measurements=(bad,),
                                           evidence_root=root)
                    self.assertIn("PAR-MEASUREMENT-INVALID",
                                  {item.rule_id for item in result.violations})
            bad_hash = replace(evidence, sha256="sha256:" + "0" * 64)
            self.assertIn("PAR-MEASUREMENT-INVALID", {
                item.rule_id for item in self._gate(
                    target, source_catalog, measurements=(bad_hash,), evidence_root=root
                )[1].violations
            })
            escaped = root.parent / "outside-parameter-evidence.bin"
            escaped.write_bytes(payload)
            try:
                fake_resolver = lambda path: escaped if path.name == "pilot.bin" else path.resolve()
                self.assertIn("PAR-MEASUREMENT-INVALID", {
                    item.rule_id for item in self._gate(
                        target, source_catalog, measurements=(evidence,), evidence_root=root,
                        resolver=fake_resolver,
                    )[1].violations
                })
                link = root / "linked.bin"
                try:
                    link.symlink_to(escaped)
                except OSError:
                    pass
                else:
                    linked = replace(evidence, locator="linked.bin")
                    self.assertIn("PAR-MEASUREMENT-INVALID", {
                        item.rule_id for item in self._gate(
                            target, source_catalog, measurements=(linked,), evidence_root=root
                        )[1].violations
                    })
            finally:
                escaped.unlink(missing_ok=True)

    def test_preregistered_factor_requires_proven_pretest_pretruth_order(self) -> None:
        _, source_catalog = self._machine()
        base = self._direct_scalar("factor", "25", Unit.PERCENT,
                                   QuantityKind.SPEED_REFERENCE, source_catalog)
        decided, decision, context = self._decide((base,), source_catalog)
        target = decided[0]
        self.assertEqual(self._gate(target, source_catalog, decisions=(decision,), context=context)[1]
                         .accountability_outcome, AccountabilityOutcome.ACCOUNTABLE)
        post_truth_approval = replace(decision, approved_at="2026-08-22T10:00:00-03:00")
        self.assertIn("PAR-DECISION-INVALID", {
            item.rule_id for item in self._gate(
                target, source_catalog, decisions=(post_truth_approval,), context=context
            )[1].violations
        })
        unresolved_use = next(item for item in source_catalog.uses  # type: ignore[attr-defined]
                              if str(item.status) == "unresolved"
                              and str(item.claim_use) == "contextual_only")
        unqualified_source = replace(decision, source_use_ids=(unresolved_use.use_id,))
        self.assertIn("PAR-DECISION-INVALID", {
            item.rule_id for item in self._gate(
                target, source_catalog, decisions=(unqualified_source,), context=context
            )[1].violations
        })
        wrong_value = replace(
            decision,
            parameter_values=(replace(decision.parameter_values[0],
                                      value=NumericValue(NumericValueKind.SCALAR, scalar="75")),),
        )
        self.assertIn("PAR-DECISION-INVALID", {
            item.rule_id for item in self._gate(
                target, source_catalog, decisions=(wrong_value,), context=context
            )[1].violations
        })
        for bad_context in (
            None,
            replace(context, test_time="2026-08-18T10:00:00-03:00"),
            replace(context, truth_time="2026-08-20T10:00:00"),
        ):
            with self.subTest(context=bad_context):
                self.assertIn("PAR-DECISION-INVALID", {
                    item.rule_id for item in self._gate(
                        target, source_catalog, decisions=(decision,), context=bad_context
                    )[1].violations
                })
        power = replace(target, quantity_kind=QuantityKind.POWER_REFERENCE)
        self.assertIn("PAR-DECISION-INVALID", {
            item.rule_id for item in self._gate(
                power, source_catalog, decisions=(decision,), context=context
            )[1].violations
        })

    def test_mock_requires_documented_unavailability_and_resolved_closure(self) -> None:
        _, source_catalog = self._machine()
        base = self._direct_scalar("mock", "4", Unit.MILLIAMPERE,
                                   QuantityKind.LOOP_CURRENT, source_catalog)
        input_parameter = self._direct_scalar(
            "mock-input", "20", Unit.MILLIAMPERE, QuantityKind.LOOP_CURRENT, source_catalog
        )
        support = next(item for item in source_catalog.uses  # type: ignore[attr-defined]
                       if str(item.claim_use) == "capability" and str(item.status) == "located")
        claim = MockSupportClaim(
            "mock-claim:test", "Documented bounded behavior", "4", Unit.MILLIAMPERE,
            QuantityKind.LOOP_CURRENT, base.experiment_scope, (support.use_id,),
        )
        admission = MockAdmission(
            mock_admission_id="mock-admission:test", record_sha256="",
            content_sha256="sha256:" + "3" * 64, owner="Emilio", approved_by="Emilio",
            approved_at="2026-08-19T10:00:00-03:00", mutable=False,
            authentic_path_assessment="Physical path unavailable in this scope.",
            authentic_feasibility=AuthenticFeasibility.UNAVAILABLE_WITH_EVIDENCE,
            reproduction_assessment_identity="sha256:" + "4" * 64,
            reproduction_disposition=ReproductionDisposition.STILL_UNAVAILABLE_WITH_EVIDENCE,
            prototype_component_id=base.prototype_component, exact_entrypoint="module:entrypoint",
            interface_schema_version="mock-interface.v1", code_identity="sha256:" + "5" * 64,
            runtime_identity="sha256:" + "6" * 64,
            configuration_identity="sha256:" + "7" * 64,
            parameter_closure_id="sha256:" + "8" * 64,
            parameter_revision_bindings=(MockParameterRevisionBinding(
                input_parameter.parameter_revision_id, input_parameter.revision_sha256
            ),),
            randomness_mode=RandomnessMode.DETERMINISTIC, seed_closure_id="not_applicable",
            seed_parameter_revision_id=None, seed_parameter_revision_sha256=None,
            permitted_output_role="mock_derived",
            permitted_output_record_family="SignalObservation.v2",
            semantic_provenance="mock_parameterized",
            emission_trace_identity="sha256:" + "9" * 64,
            simulator_profile="profile:simulator", purpose="Bounded prototype generation.",
            component=base.prototype_component, question=base.research_question,
            evidence_track=base.evidence_track, final_output=base.final_package_element,
            replacement_condition="Replace on authentic availability.", support_claims=(claim,),
            prohibited_claims=("real plant measurement",),
            prohibited_output_roles=("authentic_capture", "measured", "official_native", "official_real"),
            limitations=("Synthetic unit fixture.",),
        )
        admission = replace(admission, record_sha256=mock_admission_identity(admission))
        target = replace(
            base, parameter_class=ParameterClass.MOCK, direct_authority=None,
            mock_authority=MockAuthority(admission.mock_admission_id, claim.mock_claim_id),
            authentic_reproduction_feasibility=AuthenticFeasibility.UNAVAILABLE_WITH_EVIDENCE,
            synthetic_status="mock", revision_sha256="",
        )
        target = replace(target, revision_sha256=parameter_revision_identity(target))
        self.assertEqual(self._gate(
            target, source_catalog, other_parameters=(input_parameter,), mocks=(admission,)
        )[1]
                         .accountability_outcome, AccountabilityOutcome.ACCOUNTABLE)
        for bad in (
            replace(admission, authentic_feasibility=AuthenticFeasibility.AVAILABLE),
            replace(admission, parameter_closure_id="unresolved:parameters"),
            replace(admission, mutable=True),
        ):
            with self.subTest(admission=bad.mock_admission_id):
                self.assertIn("PAR-MOCK-INELIGIBLE", {
                    item.rule_id for item in self._gate(
                        target, source_catalog, other_parameters=(input_parameter,), mocks=(bad,)
                    )[1].violations
                })

    def test_catalog_source_identity_inventory_and_result_identity_fail_closed(self) -> None:
        machine, source_catalog = self._machine()
        target = next(item for item in machine.parameter_revisions
                      if item.parameter_id == "command.terminal53.low_current")
        catalog, result = self._gate(target, source_catalog)
        wrong = replace(catalog, source_catalog_identity="sha256:" + "0" * 64)
        wrong_required = replace(wrong.required_sets[0], catalog_identity=parameter_catalog_identity(wrong))
        wrong = replace(wrong, required_sets=(wrong_required,))
        blocked = validate_parameter_gate(wrong, source_catalog, wrong.inventories[0], wrong.required_sets[0])
        self.assertIn("PAR-BINDING-INVALID", {item.rule_id for item in blocked.violations})
        self.assertEqual(result.authorization_effect, "none")
        wording = tuple(replace(item, explanation="Different human wording.")
                        for item in blocked.violations)
        rebuilt = ParameterGateResult(
            gate_result_id=blocked.gate_result_id,
            catalog_identity=blocked.catalog_identity,
            source_catalog_identity=blocked.source_catalog_identity,
            vocabulary_version=blocked.vocabulary_version,
            inventory_id=blocked.inventory_id,
            required_set_id=blocked.required_set_id,
            temporal_context_id=blocked.temporal_context_id,
            decision_ids=blocked.decision_ids,
            measurement_evidence_ids=blocked.measurement_evidence_ids,
            mock_admission_ids=blocked.mock_admission_ids,
            validator_identity=blocked.validator_identity,
            accountability_outcome=blocked.accountability_outcome,
            violations=wording,
            limitations=blocked.limitations,
        )
        self.assertEqual(rebuilt.gate_result_id, blocked.gate_result_id)

    def test_inventory_is_independent_complete_and_exactly_bound(self) -> None:
        machine, source_catalog = self._machine()
        target = next(item for item in machine.parameter_revisions
                      if item.parameter_id == "command.terminal53.low_current")
        catalog, _ = self._gate(target, source_catalog)

        def evaluate(inventory: NumericConsumerInventory,
                     required: RequiredParameterSet) -> ParameterGateResult:
            candidate = replace(catalog, inventories=(inventory,), required_sets=(required,))
            required = replace(required, catalog_identity=parameter_catalog_identity(candidate))
            candidate = replace(candidate, required_sets=(required,))
            return validate_parameter_gate(candidate, source_catalog, inventory, required)

        inventory = catalog.inventories[0]
        required = catalog.required_sets[0]
        missing = replace(required, bindings=())
        illegal_na = replace(required, bindings=(replace(required.bindings[0],
                                                          parameter_revision_id=None,
                                                          not_applicable=True),))
        bad_dispositions = tuple(
            replace(item, state=CategoryState.NOT_APPLICABLE)
            if item.category == InventoryCategory.RANGES_ENDPOINTS else item
            for item in inventory.category_dispositions
        )
        cases = (
            (inventory, missing, "PAR-INVENTORY-INCOMPLETE"),
            (inventory, illegal_na, "PAR-BINDING-INVALID"),
            (inventory, replace(required, bindings=(replace(
                required.bindings[0], parameter_revision_sha256="sha256:" + "0" * 64
            ),)), "PAR-BINDING-INVALID"),
            (replace(inventory, category_dispositions=bad_dispositions), required,
             "PAR-INVENTORY-INCOMPLETE"),
        )
        for candidate_inventory, candidate_required, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, {
                    item.rule_id for item in evaluate(candidate_inventory, candidate_required).violations
                })

        forged_inventory = replace(inventory, requirements=())
        forged_required = replace(required, bindings=())
        forged = validate_parameter_gate(
            catalog, source_catalog, forged_inventory, forged_required
        )
        self.assertIn("PAR-SELECTION-MISMATCH", {item.rule_id for item in forged.violations})

        na_inventory = replace(
            inventory,
            requirements=(replace(inventory.requirements[0], not_applicable_allowed=True),),
        )
        na_required = replace(
            required,
            bindings=(replace(required.bindings[0], parameter_revision_id=None,
                              not_applicable=True, rationale=""),),
        )
        candidate = replace(catalog, inventories=(na_inventory,), required_sets=(na_required,))
        na_required = replace(na_required, catalog_identity=parameter_catalog_identity(candidate))
        candidate = replace(candidate, required_sets=(na_required,))
        self.assertIn("PAR-BINDING-INVALID", {
            item.rule_id for item in validate_parameter_gate(
                candidate, source_catalog, na_inventory, na_required
            ).violations
        })

    def test_conflicting_active_revisions_fail_closed(self) -> None:
        machine, source_catalog = self._machine()
        target = next(item for item in machine.parameter_revisions
                      if item.parameter_id == "command.terminal53.low_current")
        conflicting = replace(
            target, parameter_revision_id="revision:conflicting", value=NumericValue(
                NumericValueKind.SCALAR, scalar="20"
            ), direct_authority=replace(
                target.direct_authority,
                documented_value=NumericValue(NumericValueKind.SCALAR, scalar="20"),
            ),
        )
        _, result = self._gate(target, source_catalog, other_parameters=(conflicting,))
        self.assertIn("PAR-ACTIVE-CONFLICT", {item.rule_id for item in result.violations})

    def test_loader_and_cli_use_fail_closed_exit_codes(self) -> None:
        with self.assertRaises(ValueError):
            load_parameter_catalog(self.CATALOG_PATH.read_text(encoding="utf-8").replace(
                '"authorization_effect":"none"', '"authorization_effect":"none","extra":1.5', 1
            ))
        command = [
            sys.executable, "scripts/validate_parameter_evidence.py", "--catalog", str(self.CATALOG_PATH),
            "--source-catalog", str(self.SOURCE_PATH), "--consumer-inventory", str(self.CATALOG_PATH),
            "--required-set", str(self.CATALOG_PATH),
        ]
        blocked = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        malformed = subprocess.run(command[:-1] + ["missing.json"], check=False,
                                   capture_output=True, text=True)
        self.assertEqual(malformed.returncode, 2)

        machine, source_catalog = self._machine()
        target = next(item for item in machine.parameter_revisions
                      if item.parameter_id == "command.terminal53.low_current")
        accountable_catalog, _ = self._gate(target, source_catalog)
        with tempfile.TemporaryDirectory() as directory:
            catalog_path = Path(directory) / "catalog.json"
            catalog_path.write_bytes(canonical_parameter_catalog_bytes(accountable_catalog))
            accountable_command = [
                sys.executable, "scripts/validate_parameter_evidence.py", "--catalog", str(catalog_path),
                "--source-catalog", str(self.SOURCE_PATH), "--consumer-inventory", str(catalog_path),
                "--required-set", str(catalog_path),
            ]
            accountable = subprocess.run(accountable_command, check=False, capture_output=True, text=True)
            self.assertEqual(accountable.returncode, 0, accountable.stdout + accountable.stderr)

            malformed_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            malformed_payload["inventories"][0]["category_dispositions"][0]["owner_approved"] = 1
            malformed_path = Path(directory) / "malformed-types.json"
            malformed_path.write_text(json.dumps(malformed_payload), encoding="utf-8")
            malformed_command = [
                sys.executable, "scripts/validate_parameter_evidence.py",
                "--catalog", str(malformed_path), "--source-catalog", str(self.SOURCE_PATH),
                "--consumer-inventory", str(malformed_path), "--required-set", str(malformed_path),
            ]
            malformed_type = subprocess.run(
                malformed_command, check=False, capture_output=True, text=True
            )
            self.assertEqual(malformed_type.returncode, 2)
            self.assertIn("PAR-INPUT-MALFORMED", malformed_type.stdout)
            self.assertNotIn("Traceback", malformed_type.stdout + malformed_type.stderr)


if __name__ == "__main__":
    unittest.main()
