"""Edge 2 local acquisition service."""

from parallel_truth_fingerprint.edge_nodes.common.acquisition import (
    EDGE_DEVICE_CONFIGS,
    EdgeAcquisitionService,
)


class PressureEdgeService(EdgeAcquisitionService):
    """Acquire only the local pressure sensor."""

    def __init__(self) -> None:
        super().__init__(EDGE_DEVICE_CONFIGS["edge-2"])
