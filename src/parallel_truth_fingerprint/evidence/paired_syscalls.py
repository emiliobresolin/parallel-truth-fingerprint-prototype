"""Associate real Linux strace events with four-edge acquisition intervals."""
from bisect import bisect_right
import hashlib
import heapq
import json
from pathlib import Path
import re

EVENT = re.compile(r'^(\d+\.\d+)\s+([A-Za-z_][A-Za-z_0-9]*)\(')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def trace_events(path):
    """Count each syscall at entry, including unfinished calls, excluding resumes."""
    with Path(path).open(encoding='utf-8', errors='replace') as handle:
        for line in handle:
            match = EVENT.match(line)
            if match:
                yield float(match[1]), match[2]


def associate(rows, streams):
    intervals = [r['acquisition_window'] for r in rows]
    starts = [i['start_epoch'] for i in intervals]
    if any(i['start_epoch'] >= i['end_epoch'] for i in intervals) or any(
            intervals[i]['end_epoch'] > starts[i+1] for i in range(len(rows)-1)):
        raise ValueError('Acquisition intervals must be positive, ordered and disjoint.')
    tokens = [[] for _ in rows]
    for timestamp, name in heapq.merge(*streams):
        index = bisect_right(starts, timestamp)-1
        if index >= 0 and timestamp < intervals[index]['end_epoch']:
            tokens[index].append(name)
    return tokens


def export_dataset(directory):
    directory = Path(directory)
    traces = sorted((directory/'syscalls').glob('runtime.*'))
    if not traces:
        raise ValueError('Real strace output is missing.')
    rows = [json.loads(line) for profile in ('unmodulated', 'modulated')
            for line in (directory/profile/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    tokens = associate(rows, [trace_events(path) for path in traces])
    output = directory/'dataset'
    output.mkdir(exist_ok=False)
    with (output/'current-syscall-windows.jsonl').open('x', encoding='utf-8') as handle:
        for row, calls in zip(rows, tokens):
            if not calls or row['edge_membership'] != ['edge-1','edge-2','edge-3','edge-4']:
                raise ValueError('Missing kernel events or four-edge membership in a dataset row.')
            schema, vector = row['feature_schema'], row['physical_vector']
            record = {'round_id': row['round_id'], 'profile': row['profile'], 'phase': row['phase'],
                'measurement_domain': row.get('measurement_domain', 'legacy-mixed'),
                'consensus_schema': row.get('consensus_schema', 'legacy-engineering'),
                'block': row['block'], 'timestamp': row['timestamp'],
                'acquisition_window': row['acquisition_window'], 'edges': row['edge_membership'],
                'physical_currents_ma': {n.split('.')[0]: vector[i] for i,n in enumerate(schema) if n.endswith('.loop_current_ma')},
                'syscall_tokens': calls, 'syscall_scope': 'shared acquisition/runtime process and threads',
                'conditions': [v['condition'] for v in row['views']],
                'observation_source': f'{row["profile"]}/observations.jsonl'}
            handle.write(json.dumps(record, allow_nan=False)+'\n')
    manifest = {'schema': 'four-edge-current-syscall-association-v1', 'row_count': len(rows),
        'measurement_domain': rows[0].get('measurement_domain', 'legacy-mixed'),
        'consensus_schema': rows[0].get('consensus_schema', 'legacy-engineering'),
        'event_count': sum(map(len,tokens)), 'boundary_rule': 'start_epoch <= syscall entry timestamp < end_epoch',
        'capture': 'Linux strace -ff -ttt -s 0; shared runtime process, one raw file per traced PID/TID',
        'dataset_sha256': digest(output/'current-syscall-windows.jsonl'),
        'syscall_trace_sha256': {str(p.relative_to(directory)): digest(p) for p in traces}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return verify_dataset(directory)


def verify_dataset(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'dataset/manifest.json').read_text())
    if digest(directory/'dataset/current-syscall-windows.jsonl') != manifest['dataset_sha256']:
        raise ValueError('Dataset hash mismatch.')
    for name, expected in manifest['syscall_trace_sha256'].items():
        if digest(directory/name) != expected:
            raise ValueError('Raw trace hash mismatch.')
    source = {r['round_id']: r for profile in ('unmodulated','modulated')
              for r in map(json.loads,(directory/profile/'observations.jsonl').read_text().splitlines())}
    count, events, seen = 0, 0, set()
    with (directory/'dataset/current-syscall-windows.jsonl').open() as handle:
        for line in handle:
            row = json.loads(line)
            original = source[row['round_id']]
            if row['round_id'] in seen or not row['syscall_tokens'] or row['edges'] != original['edge_membership']:
                raise ValueError('Invalid/duplicate dataset association.')
            if row['acquisition_window'] != original['acquisition_window']:
                raise ValueError('Dataset acquisition window mismatch.')
            expected_currents = {n.split('.')[0]: original['physical_vector'][i] for i,n in enumerate(original['feature_schema']) if n.endswith('.loop_current_ma')}
            if row['physical_currents_ma'] != expected_currents:
                raise ValueError('Dataset currents differ from acquired values.')
            seen.add(row['round_id'])
            count += 1
            events += len(row['syscall_tokens'])
    if count != len(source) or count != manifest['row_count'] or events != manifest['event_count']:
        raise ValueError('Dataset support differs from collection.')
    return manifest
