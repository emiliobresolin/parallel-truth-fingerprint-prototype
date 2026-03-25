"""Edge node services."""

from parallel_truth_fingerprint.edge_nodes.edge_1.service import TemperatureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_2.service import PressureEdgeService
from parallel_truth_fingerprint.edge_nodes.edge_3.service import RpmEdgeService

__all__ = ["TemperatureEdgeService", "PressureEdgeService", "RpmEdgeService"]
