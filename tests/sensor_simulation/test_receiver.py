"""Mathematical verification fixtures, not approved compressor plant parameters."""

from dataclasses import FrozenInstanceError
import json
import math
import unittest

from parallel_truth_fingerprint.sensor_simulation.receiver import (
    ReceiverGasConfiguration, ReceiverGasState, advance_receiver,
)


class ReceiverGasTests(unittest.TestCase):
    def setUp(self):
        # Deliberately round test properties make independent solutions readable.
        self.gas = ReceiverGasConfiguration(
            volume_m3=2.0, specific_heat_cp_j_kg_k=1000.0,
            specific_heat_cv_j_kg_k=700.0)
        self.state = ReceiverGasState(
            configuration=self.gas, mass_kg=2.0, internal_energy_j=420000.0)

    def advance(self, state=None, **changes):
        inputs = dict(duration_seconds=10.0, inlet_mass_flow_kg_s=0.0,
                      outlet_mass_flow_kg_s=0.0, inlet_temperature_k=300.0,
                      wall_heat_flow_w=0.0)
        inputs.update(changes)
        return advance_receiver(state or self.state, **inputs)

    def assertRelative(self, actual, expected, tolerance=2e-13):
        self.assertTrue(math.isclose(actual, expected, rel_tol=tolerance, abs_tol=1e-12),
                        (actual, expected))

    def test_state_factory_observables_and_explicit_gauge_reference(self):
        state = ReceiverGasState.from_pressure_temperature(
            configuration=self.gas, pressure_abs_pa=90000.0, temperature_k=300.0)
        self.assertRelative(state.mass_kg, 2.0)
        self.assertRelative(state.internal_energy_j, 420000.0)
        self.assertRelative(state.temperature_k, 300.0)
        self.assertRelative(state.pressure_abs_pa, 90000.0)
        self.assertRelative(state.gauge_pressure_pa(ambient_pressure_pa=100000.0), -10000.0)
        with self.assertRaises(TypeError):
            state.gauge_pressure_pa()

    def test_state_and_configuration_immutable_and_serializable(self):
        before = self.state.to_dict()
        self.assertEqual(json.loads(json.dumps(before)), before)
        self.assertEqual(before['configuration']['temperature_measurement_point'], 'receiver_gas')
        with self.assertRaises(FrozenInstanceError):
            self.state.mass_kg = 3.0
        with self.assertRaises(FrozenInstanceError):
            self.gas.volume_m3 = 3.0
        detached = self.state.to_dict()
        detached['configuration']['assumptions'].append('changed')
        self.assertEqual(self.state.to_dict(), before)

    def test_closed_adiabatic_volume_unchanged(self):
        result = self.advance()
        self.assertEqual(result, self.state)
        self.assertIsNot(result, self.state)

    def test_closed_volume_heating_and_cooling_known_energy_balance(self):
        for heat in (-1000.0, 2000.0):
            with self.subTest(heat=heat):
                result = self.advance(wall_heat_flow_w=heat)
                expected_energy = 420000.0 + heat * 10.0
                self.assertRelative(result.internal_energy_j, expected_energy)
                self.assertRelative(result.temperature_k, expected_energy / 1400.0)
                self.assertRelative(result.pressure_abs_pa,
                                    90000.0 * expected_energy / 420000.0)

    def test_equal_flow_at_inlet_temperature_is_equilibrium(self):
        result = self.advance(inlet_mass_flow_kg_s=0.02, outlet_mass_flow_kg_s=0.02)
        self.assertRelative(result.mass_kg, self.state.mass_kg)
        self.assertRelative(result.internal_energy_j, self.state.internal_energy_j)
        self.assertRelative(result.temperature_k, 300.0)

    def test_balanced_flow_relaxation_known_exponential(self):
        result = self.advance(inlet_mass_flow_kg_s=0.02, outlet_mass_flow_kg_s=0.02,
                              inlet_temperature_k=350.0, wall_heat_flow_w=100.0)
        # m fixed; dT/dt = q*cp/(m*cv) * (Tin + Q/(q*cp) - T).
        target = 355.0
        expected_temperature = target + (300.0 - target) * math.exp(-0.02 * 1000 / 1400 * 10)
        self.assertRelative(result.temperature_k, expected_temperature)

    def test_adiabatic_filling_known_enthalpy_integral(self):
        result = self.advance(inlet_mass_flow_kg_s=0.02, inlet_temperature_k=400.0)
        self.assertRelative(result.mass_kg, 2.2)
        self.assertRelative(result.internal_energy_j, 420000.0 + 0.02 * 1000 * 400 * 10)

    def test_adiabatic_emptying_known_power_law(self):
        result = self.advance(outlet_mass_flow_kg_s=0.02)
        gamma = 1000.0 / 700.0
        self.assertRelative(result.mass_kg, 1.8)
        self.assertRelative(result.temperature_k, 300.0 * (1.8 / 2.0) ** (gamma - 1))
        self.assertRelative(result.internal_energy_j, 420000.0 * (1.8 / 2.0) ** gamma)

    def test_general_constant_boundary_matches_subdivision(self):
        boundaries = dict(inlet_mass_flow_kg_s=0.03, outlet_mass_flow_kg_s=0.02,
                          inlet_temperature_k=370.0, wall_heat_flow_w=-120.0)
        full = self.advance(duration_seconds=100.0, **boundaries)
        divided = self.state
        for _ in range(100):
            divided = self.advance(divided, duration_seconds=1.0, **boundaries)
        self.assertRelative(full.mass_kg, divided.mass_kg)
        self.assertRelative(full.internal_energy_j, divided.internal_energy_j)
        self.assertRelative(full.temperature_k, divided.temperature_k)

    def test_general_energy_solution_from_integrating_factor(self):
        result = self.advance(duration_seconds=100.0, inlet_mass_flow_kg_s=0.03,
                              outlet_mass_flow_kg_s=0.02, inlet_temperature_k=370.0,
                              wall_heat_flow_w=-120.0)
        # Independent energy-form integrating factor, avoiding the implementation's
        # temperature-form expm1/log1p evaluation.
        a = 0.03 - 0.02
        b = (1000.0 / 700.0) * 0.02
        factor = (3.0 / 2.0) ** (-b / a)
        incoming_power = 0.03 * 1000.0 * 370.0 - 120.0
        expected_energy = 420000.0 * factor + incoming_power / (a + b) * (3.0 - 2.0 * factor)
        self.assertRelative(result.mass_kg, 3.0)
        self.assertRelative(result.internal_energy_j, expected_energy)

    def test_nearly_balanced_flow_continuous_at_zero_imbalance(self):
        balanced = self.advance(inlet_mass_flow_kg_s=0.02, outlet_mass_flow_kg_s=0.02,
                                inlet_temperature_k=360.0)
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                near = self.advance(inlet_mass_flow_kg_s=0.02 + direction * 1e-15,
                                    outlet_mass_flow_kg_s=0.02, inlet_temperature_k=360.0)
                self.assertRelative(near.internal_energy_j, balanced.internal_energy_j)
                self.assertRelative(near.temperature_k, balanced.temperature_k)

    def test_tiny_steps_and_nearly_equal_specific_heats(self):
        gas = ReceiverGasConfiguration(volume_m3=2.0, specific_heat_cp_j_kg_k=700.000000000001,
                                       specific_heat_cv_j_kg_k=700.0)
        state = ReceiverGasState(configuration=gas, mass_kg=2.0, internal_energy_j=420000.0)
        result = self.advance(state, duration_seconds=1e-6, outlet_mass_flow_kg_s=0.02)
        self.assertRelative(result.temperature_k, state.temperature_k)
        self.assertRelative(result.internal_energy_j,
                            state.internal_energy_j * (result.mass_kg / state.mass_kg)
                            ** (gas.specific_heat_cp_j_kg_k / gas.specific_heat_cv_j_kg_k))

    def test_no_clipping_to_legacy_transmitter_spans(self):
        state = ReceiverGasState.from_pressure_temperature(
            configuration=self.gas, pressure_abs_pa=3000000.0, temperature_k=600.0)
        result = self.advance(state, wall_heat_flow_w=1000.0)
        self.assertGreater(result.temperature_k - 273.15, 95.0)
        self.assertGreater(result.pressure_abs_pa / 100000.0, 8.5)
        self.assertRelative(result.internal_energy_j, state.internal_energy_j + 10000.0)

    def test_configuration_rejects_invalid_numbers_and_properties(self):
        defaults = dict(volume_m3=2.0, specific_heat_cp_j_kg_k=1000.0,
                        specific_heat_cv_j_kg_k=700.0)
        for field in defaults:
            for invalid in (None, True, '2', math.nan, math.inf, -math.inf, 0.0, -1.0):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    ReceiverGasConfiguration(**dict(defaults, **{field: invalid}))
        for cp in (699.0, 700.0):
            with self.subTest(cp=cp), self.assertRaises(ValueError):
                ReceiverGasConfiguration(**dict(defaults, specific_heat_cp_j_kg_k=cp))

    def test_state_rejects_invalid_numbers_and_overflow(self):
        for field in ('mass_kg', 'internal_energy_j'):
            for invalid in (None, True, '2', math.nan, math.inf, -math.inf, 0.0, -1.0):
                args = dict(configuration=self.gas, mass_kg=2.0, internal_energy_j=420000.0)
                args[field] = invalid
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    ReceiverGasState(**args)
        with self.assertRaises(ValueError):
            ReceiverGasState(configuration=None, mass_kg=2.0, internal_energy_j=420000.0)
        with self.assertRaises(ValueError):
            ReceiverGasState(configuration=self.gas, mass_kg=1e-300, internal_energy_j=1e300)

    def test_factory_and_gauge_validate_all_explicit_inputs(self):
        defaults = dict(configuration=self.gas, pressure_abs_pa=90000.0, temperature_k=300.0)
        for field in ('pressure_abs_pa', 'temperature_k'):
            for invalid in (None, True, '2', math.nan, math.inf, -math.inf, 0.0, -1.0):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    ReceiverGasState.from_pressure_temperature(**dict(defaults, **{field: invalid}))
        for invalid in (None, True, '2', math.nan, math.inf, -math.inf, 0.0, -1.0):
            with self.subTest(ambient=invalid), self.assertRaises(ValueError):
                self.state.gauge_pressure_pa(ambient_pressure_pa=invalid)
        with self.assertRaises(ValueError):
            ReceiverGasState.from_pressure_temperature(**dict(defaults, configuration=None))
        tiny_gas = ReceiverGasConfiguration(volume_m3=1.0,
            specific_heat_cp_j_kg_k=2e-300, specific_heat_cv_j_kg_k=1e-300)
        with self.assertRaises(ValueError):
            ReceiverGasState.from_pressure_temperature(configuration=tiny_gas,
                                                       pressure_abs_pa=1.0, temperature_k=1e-300)

    def test_invalid_boundary_inputs_leave_original_state_intact(self):
        before = self.state.to_dict()
        fields = ('duration_seconds', 'inlet_mass_flow_kg_s', 'outlet_mass_flow_kg_s',
                  'inlet_temperature_k', 'wall_heat_flow_w')
        for field in fields:
            for invalid in (None, True, '2', math.nan, math.inf, -math.inf):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    self.advance(**{field: invalid})
                self.assertEqual(self.state.to_dict(), before)
        for field in fields[:-1]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.advance(**{field: -1.0})
        for field in ('duration_seconds', 'inlet_temperature_k'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.advance(**{field: 0.0})

    def test_mass_exhaustion_and_nonpositive_energy_rejected_atomically(self):
        before = self.state.to_dict()
        for boundaries in (dict(outlet_mass_flow_kg_s=0.2),
                           dict(outlet_mass_flow_kg_s=0.3),
                           dict(wall_heat_flow_w=-42000.0),
                           dict(wall_heat_flow_w=-50000.0)):
            with self.subTest(boundaries=boundaries), self.assertRaises(ValueError):
                self.advance(**boundaries)
            self.assertEqual(self.state.to_dict(), before)

    def test_intermediate_inlet_enthalpy_underflow_is_rejected_atomically(self):
        # The exact filling increment is 1 J. Losing qin*cp before multiplying
        # by Tin would silently return 150 J instead of 151 J.
        gas = ReceiverGasConfiguration(volume_m3=1.0,
                                       specific_heat_cp_j_kg_k=1e-200,
                                       specific_heat_cv_j_kg_k=5e-201)
        state = ReceiverGasState(configuration=gas, mass_kg=1e200,
                                 internal_energy_j=150.0)
        before = state.to_dict()
        with self.assertRaisesRegex(ValueError, 'enthalpy underflows'):
            self.advance(state, duration_seconds=1e200,
                         inlet_mass_flow_kg_s=1e-200,
                         inlet_temperature_k=1e200)
        self.assertEqual(state.to_dict(), before)

    def test_arithmetic_overflow_is_explicit_rejection(self):
        before = self.state.to_dict()
        for boundaries in (dict(inlet_mass_flow_kg_s=1e308),
                           dict(outlet_mass_flow_kg_s=1e308),
                           dict(duration_seconds=1e308, wall_heat_flow_w=1e308),
                           dict(inlet_mass_flow_kg_s=1.0, inlet_temperature_k=1e308)):
            with self.subTest(boundaries=boundaries), self.assertRaises(ValueError):
                self.advance(**boundaries)
            self.assertEqual(self.state.to_dict(), before)


if __name__ == '__main__':
    unittest.main()
