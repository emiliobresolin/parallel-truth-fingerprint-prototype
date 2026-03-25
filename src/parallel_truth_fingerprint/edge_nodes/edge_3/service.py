"""Edge 3 local acquisition service."""

from parallel_truth_fingerprint.edge_nodes.common.acquisition import (
    EDGE_DEVICE_CONFIGS,
    EdgeAcquisitionService,
)


class RpmEdgeService(EdgeAcquisitionService):
    """Acquire only the local RPM sensor."""

    def __init__(self) -> None:
        super().__init__(EDGE_DEVICE_CONFIGS["edge-3"])
