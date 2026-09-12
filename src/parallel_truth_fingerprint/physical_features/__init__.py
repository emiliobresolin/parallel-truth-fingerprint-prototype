"""Versioned, pure physical-feature schema and projection contracts."""

from .schema import (
    FeatureDefinition,
    FeatureSchema,
    FeatureSchemaError,
    FeatureValue,
    LegacyBaselineCatalogue,
    OperatingContextValue,
    PhysicalFeatureRow,
    build_physical_features,
    register_physical_feature_schema,
    validate_physical_feature_schema,
)

__all__ = [
    "FeatureDefinition", "FeatureSchema", "FeatureSchemaError", "FeatureValue", "LegacyBaselineCatalogue",
    "OperatingContextValue", "PhysicalFeatureRow", "build_physical_features",
    "register_physical_feature_schema", "validate_physical_feature_schema",
]
