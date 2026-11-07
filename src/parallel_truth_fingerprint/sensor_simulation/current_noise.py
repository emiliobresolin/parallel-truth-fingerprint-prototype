"""Sample-domain current noise scaled by a published transmitter measurement.

TI SLAAE91 (March 2023), Table 1-2, reports 782 nA RMS at static 3 mA,
measured with a 24-bit 31-kSPS ADC. Gaussianity, independent samples/channels
and constant RMS throughout 4--20 mA are explicit emulation assumptions.
The ADC rate is acquisition context, not an inferred analog noise bandwidth.
"""
from dataclasses import asdict, dataclass
import hashlib
import math
import random


@dataclass(frozen=True)
class CurrentNoiseConfiguration:
    model: str = 'ti-slaae91-sampled-gaussian-v1'
    distribution: str = 'independent zero-mean Gaussian samples per channel'
    rms_ma: float = 782e-6
    source: str = 'Texas Instruments SLAAE91, March 2023, Table 1-2'
    source_url: str = 'https://www.ti.com/document-viewer/lit/html/slaae91'
    gaussian_model_reference_url: str = 'https://wiki.analog.com/university/labs/noise_adalm2000'
    rms_standard_deviation_reference_url: str = 'https://www.ti.com/lit/an/slva043b/slva043b.pdf'
    reference_current_ma: float = 3.0
    reference_adc_bits: int = 24
    reference_adc_samples_per_second: int = 31000
    reference_sample_count: int = 16383
    bandwidth_hz: float | None = None
    modeling_assumptions: str = (
        'Reference-circuit RMS applied constantly over the nominal current range; '
        'Gaussian independent samples/channels are a sample-domain approximation, '
        'not a measured spectral fit or commercial-instrument noise specification.'
    )
    output_policy: str = 'Add noise before nominal 4..20 mA saturation; no current rounding.'


def noise_configuration() -> dict[str, object]:
    """Fresh JSON-serializable configuration for frozen protocols and frames."""
    return asdict(CurrentNoiseConfiguration())


def validate_noise_configuration(frozen: object) -> None:
    if frozen != noise_configuration():
        raise ValueError('Current-noise configuration differs from frozen protocol.')


def noise_rms_ma(multiplier: float = 1.0) -> float:
    if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
        raise ValueError('Current-noise multiplier must be a finite nonnegative number.')
    if not math.isfinite(multiplier) or multiplier < 0:
        raise ValueError('Current-noise multiplier must be a finite nonnegative number.')
    rms = CurrentNoiseConfiguration().rms_ma * multiplier
    if not math.isfinite(rms):
        raise ValueError('Current-noise RMS must be finite.')
    return rms


class SampledCurrentNoise:
    """Independent reproducible channel streams; no process RNG consumption."""

    def __init__(self, seed: int | None):
        self._seed = seed if seed is not None else random.SystemRandom().getrandbits(256)
        self._streams: dict[str, random.Random] = {}

    def sample_ma(self, channel: str, *, multiplier: float = 1.0) -> float:
        rms = noise_rms_ma(multiplier)
        if channel not in self._streams:
            token = f'ti-slaae91-sampled-gaussian-v1:{self._seed}:{channel}'.encode('utf-8')
            self._streams[channel] = random.Random(int.from_bytes(hashlib.sha256(token).digest(), 'big'))
        # Consume one standardized sample even for a disabled control, so a
        # multiplier change does not shift the subsequent channel sequence.
        return self._streams[channel].gauss(0.0, 1.0) * rms
