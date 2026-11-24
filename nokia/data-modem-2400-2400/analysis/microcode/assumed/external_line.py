"""Explicit cycle-timed digital input; no program-counter branch overrides."""
from bisect import bisect_right


def validate_external_line(policy):
    if not isinstance(policy,dict):
        if policy not in (0,1):raise ValueError('invalid external input bit')
        return
    if (policy.get('mode')!='cycle-events' or policy.get('status') not in ('stub','hypothesis','recovered-from-data')
            or not policy.get('evidence') or policy.get('initial') not in (0,1) or not isinstance(policy.get('events'),list)):
        raise ValueError('external line requires cycle-events, initial bit and provenance')
    previous=-1
    for event in policy['events']:
        if (not isinstance(event,list) or len(event)!=2 or type(event[0]) is not int or event[0]<=previous
                or event[1] not in (0,1)):
            raise ValueError('external line events require increasing nonnegative integer cycles and bit values')
        previous=event[0]


def external_line_value(policy,cycle):
    if not isinstance(policy,dict):return policy,None
    events=policy['events'];index=bisect_right([event[0] for event in events],cycle)-1
    value=policy['initial'] if index<0 else events[index][1]
    return value,dict(value=value,event_index=index,event_cycle=None if index<0 else events[index][0],
                      status=policy['status'],evidence=policy['evidence'])


def external_line_phase(policy,next_cycle):
    """Time cannot be discarded while a future scheduled change can break a loop."""
    if not isinstance(policy,dict):return None
    return min(next_cycle,policy['events'][-1][0] if policy['events'] else 0)
