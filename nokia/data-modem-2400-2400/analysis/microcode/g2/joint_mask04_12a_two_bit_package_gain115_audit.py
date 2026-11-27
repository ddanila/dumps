"""Audit matched 1.0x/1.15x package-route transfer and latch staging."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_two_bit_package_route2 import CAPTURES, FEATURES, STEPS, gate_phase
from joint_mask04_12a_two_bit_package_latch import staged_code

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
LOW_SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-route2-holdout.json'
HIGH_SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-route2-gain115.json'
PRIOR_GRAPH = RESULTS / 'joint-mask04-12a-two-bit-package-holdout-audit.json'
LOW_RAW = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-route2-holdout-{n}.json'
                for n in (165, 167))
HIGH_RAW = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-route2-gain115-{n}.json'
                 for n in (165, 167))
OUT = RESULTS / 'joint-mask04-12a-two-bit-package-gain115-audit.json'


def run(out=OUT):
    low = json.loads(LOW_SUMMARY.read_text())['cases']
    high = json.loads(HIGH_SUMMARY.read_text())['cases']
    if len(low) != len(high) or len(high) != 4:
        raise ValueError('matched case count changed')
    pairs = []
    for a, b in zip(low, high):
        row = dict(carrier_offset=a['carrier_offset'], selector=a['selector'],
                   payloads_match=a['payload'] == b['payload'],
                   tx_trace_match=a['tx_trace_digest'] == b['tx_trace_digest'],
                   rx_trace_changed=a['rx_trace_digest'] != b['rx_trace_digest'],
                   pcm_changed=a['pcm_sha256'] != b['pcm_sha256'],
                   gain1_exact=(not a['gate_wrong_indices'] and
                                a['recovered_matches_offered'] and
                                a['controller_matches_payload']),
                   gain115_unseen_keys=b['unseen_keys'],
                   gain115_wrong_dibits=len(b['gate_wrong_indices']),
                   gain115_exact_line=b['recovered_matches_offered'],
                   gain115_exact_payload=b['controller_matches_payload'],
                   gain115_clipped_samples=b['clipped_samples'])
        if (not all(row[k] for k in ('payloads_match', 'tx_trace_match',
                                     'rx_trace_changed', 'pcm_changed',
                                     'gain1_exact', 'gain115_exact_line',
                                     'gain115_exact_payload')) or
                row['gain115_unseen_keys'] != ['091', '0D1', '125', '1FD'] or
                row['gain115_wrong_dibits'] or row['gain115_clipped_samples']):
            raise ValueError(('matched gain transfer changed', row))
        pairs.append(row)
    cases = [case for path in (*CAPTURES, *LOW_RAW, *HIGH_RAW)
             for case in json.loads(path.read_text())['cases']]
    graph = solve(cases, FEATURES, STEPS)
    if (len(cases), graph['state_codes'],
            graph['directed_conflicts'], graph['components']) != (54, 50, 0, [50]):
        raise ValueError('joined phase graph changed')
    prior = json.loads(PRIOR_GRAPH.read_text())['phase_graph']['relative_phase']
    new = {key: dict(inferred_phase=value,
                     gate_phase=(gate_phase(int(key, 16)) - 1) & 3)
           for key, value in graph['relative_phase'].items() if key not in prior}
    if new != {key: dict(inferred_phase=phase, gate_phase=phase)
               for key, phase in [('035', 1), ('091', 0), ('0D1', 0),
                                  ('125', 1), ('1FD', 2)]}:
        raise ValueError('unseen-key phase predictions changed')
    stage_mismatches = 0
    row_shifts = 0
    for path in HIGH_RAW:
        for case in json.loads(path.read_text())['cases']:
            for symbol in case['multi_visit_symbols']:
                stage_mismatches += staged_code(symbol) != code(symbol, FEATURES)
                row_shifts += bool((symbol['visits']['46']['row0'] ^
                                    symbol['visits']['47']['row0']) & 3)
    if stage_mismatches or row_shifts:
        raise ValueError('high-gain staged latch changed')
    paths = (Path(__file__), LOW_SUMMARY, HIGH_SUMMARY, PRIOR_GRAPH,
             *CAPTURES, *LOW_RAW, *HIGH_RAW,
             HERE / 'joint_mask04_12a_two_bit_package_route2.py',
             HERE / 'joint_mask04_12a_two_bit_package_route2_gain115.py',
             HERE / 'joint_mask04_12a_two_bit_package_latch.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='matched high-gain package-route and latch audit',
                  matched_cases=pairs, phase_graph=graph,
                  new_key_predictions=new,
                  high_gain_staged_symbols=260,
                  high_gain_staged_state_mismatches=stage_mismatches,
                  high_gain_row0_y01_shifts=row_shifts,
                  limitations=[
                      'The high-gain runs are genuine frozen-gate tests; the joined graph is a retrospective consistency audit.',
                      'Photographed package capacity does not identify the actual Nokia data, enable, analog or serial nets.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('matched', len(report['matched_cases']), 'graph',
          report['phase_graph']['state_codes'], 'stage mismatches',
          report['high_gain_staged_state_mismatches'])
