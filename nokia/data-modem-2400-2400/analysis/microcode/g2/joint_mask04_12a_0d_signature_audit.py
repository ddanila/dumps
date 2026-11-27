"""Compare old and new state-0D five-visit signatures at fixed modes."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OLD = RESULTS / 'joint-mask04-12a-visit94-old0d-replay.json'
EDGE = RESULTS / 'joint-mask04-12a-visit94-gain07-challenge-0.7.json'
HELD = RESULTS / 'joint-mask04-12a-visit94-mode81-control-expanded.json'
GRAPH = RESULTS / 'joint-mask04-12a-visit94-gain07-graph-audit.json'
OUT = RESULTS / 'joint-mask04-12a-0d-signature-audit.json'
VISITS = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8')


def new_occurrences(path):
    found = []
    for case in json.loads(path.read_text())['cases']:
        for index, symbol in enumerate(case['multi_visit_symbols']):
            if sample_state(symbol, SELECTED) == 0x0D:
                found.append(dict(selector=case['selector'], symbol=index,
                                  visits=symbol['visits']))
    return found


def bit_counts(rows, visit, site, bit):
    return {str(value): count for value, count in sorted(Counter(
        (row['visits'][visit][site] >> bit) & 1 for row in rows).items())}


def run(out=OUT):
    older = json.loads(OLD.read_text())
    old = {case['mode']: case['state_0d_occurrences']
           for case in older['cases']}
    new = dict(held_81=new_occurrences(HELD),
               edge_81_A1=new_occurrences(EDGE))
    if ([(mode, len(old[mode]), len(new[mode])) for mode in old] !=
            [('held_81', 43, 18), ('edge_81_A1', 32, 18)]):
        raise ValueError('0D comparison population changed')
    comparisons = {}
    for mode in old:
        separated = []
        for visit in VISITS:
            for site in SITES:
                for bit in range(8):
                    before = bit_counts(old[mode], visit, site, bit)
                    after = bit_counts(new[mode], visit, site, bit)
                    if len(before) == len(after) == 1 and set(before) != set(after):
                        separated.append(dict(visit=visit, site=site,
                                              bit=bit, older=before, newer=after))
        comparisons[mode] = dict(older_occurrences=len(old[mode]),
                                 newer_occurrences=len(new[mode]),
                                 stable_separating_bits=separated,
                                 first_y4=dict(older=bit_counts(old[mode], '46', 'y3f8', 4),
                                               newer=bit_counts(new[mode], '46', 'y3f8', 4)),
                                 row0_bit1=dict(older=bit_counts(old[mode], '46', 'row0', 1),
                                                newer=bit_counts(new[mode], '46', 'row0', 1)),
                                 later_y6=dict(older=bit_counts(old[mode], '94', 'y3f8', 6),
                                               newer=bit_counts(new[mode], '94', 'y3f8', 6)))
    for mode in comparisons:
        group = comparisons[mode]
        if (group['first_y4'] != dict(older={'0': group['older_occurrences']},
                                     newer={'1': group['newer_occurrences']}) or
                group['row0_bit1'] != dict(older={'1': group['older_occurrences']},
                                          newer={'0': group['newer_occurrences']})):
            raise ValueError(('0D early-bit separation changed', mode))
    graph = json.loads(GRAPH.read_text())
    if (graph['older_label_disagreements'] != {'0D': {'older': 1, 'new': 0}} or
            graph['per_state']['0D']['visit94_y6'] != 1):
        raise ValueError('phase-0D label comparison changed')
    paths = (Path(__file__), OLD, EDGE, HELD, GRAPH,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py')
    report = dict(experiment='older/newer state-0D full-capture feature audit',
                  fixture=dict(older_carrier_offset=112,
                               newer_carrier_offset=141,
                               newer_gain_factor=0.7,
                               modes=['held_81', 'edge_81_A1'],
                               inspected_visits=VISITS, sites=SITES,
                               older_inferred_phase=1, newer_inferred_phase=0),
                  comparisons=comparisons,
                  limitations=[
                      'The phase labels use offered dibits and the assumed line and capture routes.',
                      'Stable separation of this one state is not a complete receive classifier or a physical net identification.',
                      'A new first-Y or row bit would need storage, gate-capacity and fresh-stream validation.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print({mode: len(c['stable_separating_bits'])
           for mode, c in report['comparisons'].items()})
