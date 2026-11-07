"""Acquired-current boundary: compare digital copies of one source observation."""
import hashlib
import json
import math

DOMAIN = 'loop_current_ma'
SCHEMA = 'current-consensus-v2'
SPAN_MA = 16.0


def raw_current(payload):
    if isinstance(payload.process_data.loop_current_ma, bool):
        raise ValueError('Boolean values are not acquired currents.')
    try:
        value = float(payload.process_data.loop_current_ma)
    except (TypeError, ValueError) as error:
        raise ValueError('An acquired numeric current is required.') from error
    if not math.isfinite(value):
        raise ValueError('Acquired current must be finite.')
    return value


def source_event_id(payload):
    identity = [payload.gateway_id, payload.device_info.tag, payload.timestamp]
    if any(not isinstance(v, str) or not v for v in identity):
        raise ValueError('Acquisition source identity is required.')
    secondary = payload.process_data.sv
    if secondary is not None and secondary.description == 'Totalizer_1_Mass':
        if (payload.device_info.tag != 'FIT-101' or secondary.unit != 'kg'
                or isinstance(secondary.value, bool) or not isinstance(secondary.value, (int, float))
                or not math.isfinite(secondary.value) or secondary.value < 0):
            raise ValueError('FIT-101 Totalizer1 requires finite nonnegative kg and documented identity.')
        identity.append({'hart_totalizer1': {'value': float(secondary.value), 'unit': secondary.unit,
                         'description': secondary.description, 'unit_code': secondary.unit_code}})
    return hashlib.sha256(json.dumps(identity, ensure_ascii=True, separators=(',', ':')).encode('ascii')).hexdigest()


def same_observation(left, right):
    return source_event_id(left) == source_event_id(right) and raw_current(left) == raw_current(right)


def diagnostic_round(value):
    """Match Go math.Round for nonnegative diagnostic quantities, without overflow."""
    if not math.isfinite(value):
        raise ValueError('Current diagnostic calculation overflowed.')
    if value >= 2**43:
        return value
    return math.floor(value*1000 + .5)/1000
