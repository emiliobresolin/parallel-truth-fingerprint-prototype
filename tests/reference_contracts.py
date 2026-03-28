"""Test-only HART-inspired reference semantics for Story 1.6."""

HART_TRANSMITTER_REFERENCE = {
    "temperature": {
        "pv_description": "Process_Temperature",
        "sv_optional": True,
        "expected_sv_description": "Sensor_Body_Temperature",
    },
    "pressure": {
        "pv_description": "Process_Pressure",
        "sv_optional": True,
        "expected_sv_description": "Transmitter_Module_Temperature",
    },
    "rpm": {
        "pv_description": "Shaft_Speed",
        "sv_optional": True,
        "expected_sv_description": None,
    },
}
