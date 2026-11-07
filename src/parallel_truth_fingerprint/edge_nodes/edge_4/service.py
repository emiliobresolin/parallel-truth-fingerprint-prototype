"""Fourth edge: HART thermal mass flowmeter on the compressed-air delivery line."""
from parallel_truth_fingerprint.config.ranges import SensorRange
from parallel_truth_fingerprint.edge_nodes.common.acquisition import EdgeDeviceConfig, EdgeAcquisitionService


class MassFlowEdgeService(EdgeAcquisitionService):
    """Read FIT-101, an emulated Endress+Hauser t-mass F 300 HART."""

    def __init__(self):
        from parallel_truth_fingerprint.sensor_simulation.mass_flow import MassFlowCompressorSimulator
        super().__init__(EdgeDeviceConfig(edge_id='edge-4', gateway_id='GW-EDGE-04',
            sensor_name='mass_flow', tag='FIT-101', long_tag='Compressed_Air_Mass_Flow',
            manufacturer_id=0x11, device_type=0x1160, unit='kg/h', unit_code=None,
            sensor_range=SensorRange(0.0, 1000.0)),
            simulator=MassFlowCompressorSimulator(modulated=False, sample_seconds=5/3, seed=101))
