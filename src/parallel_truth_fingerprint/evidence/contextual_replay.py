"""Build paired physical/supervisory histories without attack labels as features."""
import math

CONDITIONS = ('normal_stable','legitimate_transition','replay_same_regime','replay_hiding_change')


def scaled(vector, indices):
    values = [(float(vector[i])-4.)/16. for i in indices]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Non-finite current input.')
    return values


def test_windows(rows, indices):
    """Each phase/block is a separate counterfactual episode starting from live history.

    After onset, each branch carries its own supervisory history, including replay.
    Physical history always remains current. Labels identify histories for bookkeeping
    and metrics only; the input consists exclusively of normalized current values.
    """
    history, result = {}, []
    previous = None
    for row in rows:
        physical = scaled(row['physical_vector'],indices)
        if row['views'] and previous is None:
            raise ValueError('Missing physical history.')
        if previous is not None and row['index'] != previous['index']+1:
            raise ValueError('Non-contiguous physical observations.')
        for view in row['views']:
            condition = view['condition']
            if condition not in CONDITIONS:
                raise ValueError('Unknown paired condition.')
            key = (row['phase'],row['block'],condition)
            if row['offset'] == 0:
                prior_supervisory = scaled(previous['physical_vector'],indices)
                prior_source = previous['round_id']
            else:
                if key not in history or history[key][0] != row['offset']-1:
                    raise ValueError('Supervisory history skipped an episode observation.')
                _, prior_supervisory, prior_source = history[key]
            supervisory = scaled(view['supervisory_vector'],indices)
            prior_physical = scaled(previous['physical_vector'],indices)
            window = [prior_physical+prior_supervisory,physical+supervisory]
            current_source = (view['historical_state']['source_round_id']
                              if view.get('historical_state') else row['round_id'])
            history[key] = (row['offset'],supervisory,current_source)
            result.append({'round_id':row['round_id'],'previous_physical_round_id':previous['round_id'],
                'block':row['block'],'offset':row['offset'],'condition':condition,
                'boundary':row['offset']==0,'supervisory_source_ids':[prior_source,current_source],
                'input_window':window,'comparator_anomalous':bool(view['comparison']['divergent_sensors'])})
        previous = row
    return result


def metrics(records, field, exclude_boundary=False):
    result = {}
    for condition in CONDITIONS:
        selected = [r for r in records if r['condition']==condition and (not exclude_boundary or not r['boundary'])]
        alerts = sum(bool(r[field]) for r in selected)
        result[condition] = {'count':len(selected),'alerts':alerts,
            'rate':alerts/len(selected) if selected else None,
            'rate_role':'recall' if condition.startswith('replay_') else 'false_positive_rate'}
    return result
