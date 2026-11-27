"""Capture visit 94 on the older passing answer stream containing state 0D."""

import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_phase_holdout as old
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_12a_visit94_phase_gate as gate
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_visit94_phase_gate import candidate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
PRIOR = RESULTS / 'joint-mask04-12a-mode-phase-holdout.json'
OUT = RESULTS / 'joint-mask04-12a-visit94-old0d-replay.json'


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    captures = []
    original = old.execute_case
    def collecting(*args, **kwargs):
        result = original(*args, **kwargs)
        captures.append(result[2])
        return result
    with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
            patch.object(old, 'execute_case', collecting):
        replay = old.run(out=RESULTS / 'joint-mask04-12a-visit94-old0d-expanded.json')
    if len(captures) != 2 or len(replay['cases']) != len(prior['cases']):
        raise ValueError('old 0D capture count changed')
    rows = []
    answer = next(case for case in json.loads(old.SOURCE.read_text())['cases']
                  if case['selector'] == '60')
    inverse = {step: dibit for dibit, step in
               enumerate(prior['fixture']['phase_convention'])}
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        if controller_sha != replay['fixture']['controller_probe_sha256']:
            raise ValueError('controller probe changed')
        def captured(symbol, variant, covers):
            return candidate_phase(symbol), gate.READY, sample_state(symbol, SELECTED)
        with patch.object(serial, 'captured_phase', captured):
            for case, earlier, symbols in zip(replay['cases'], prior['cases'], captures):
                for key in ('mode', 'rx_trace_digest', 'pc_digest', 'gate_edges',
                            'observed_states', 'frozen_gate_wrong_indices',
                            'recovered_matches_offered', 'controller_decoded_bytes'):
                    if case[key] != earlier[key]:
                        raise ValueError(('old answer run changed', key))
                occurrences = []
                for index in range(65):
                    symbol = symbols[index]
                    if sample_state(symbol, SELECTED) == 0x0D:
                        occurrences.append(dict(symbol=index,
                                                visit94_y=f"{symbol['visits']['94']['y3f8']:02X}",
                                                visit94_y6=(symbol['visits']['94']['y3f8'] >> 6) & 1,
                                                visits={visit: symbol['visits'][visit]
                                                        for visit in ('46', '47', '93', '94', '141')},
                                                candidate_phase=candidate_phase(symbol)))
                if not occurrences:
                    raise ValueError(('old 0D missing', case['mode']))
                compared = dict(multi_visit_symbols=[symbols[i] for i in range(65)],
                                expected_dibits=answer['expected_dibits'],
                                selector='60', payload=answer['payload'],
                                offered_line_bytes=answer['offered_line_bytes'])
                score = serial.replay(compared, serial.VARIANTS['aligned'],
                                      None, inverse, exe)
                rows.append(dict(mode=case['mode'],
                                 rx_trace_digest=case['rx_trace_digest'],
                                 expected_dibits=answer['expected_dibits'],
                                 multi_visit_symbols=[symbols[i] for i in range(65)],
                                 state_0d_occurrences=occurrences,
                                 state_0d_visit94_y6_counts={str(bit): count
                                     for bit, count in sorted(Counter(
                                         item['visit94_y6'] for item in occurrences).items())},
                                 candidate_wrong_indices=score['wrong_decision_indices'],
                                 candidate_recovered_matches_offered=score['recovered_matches_offered'],
                                 candidate_controller_decoded_bytes=score['controller_decoded_bytes'],
                                 candidate_controller_errors=score['controller_errors']))
    if {item['visit94_y6'] for item in rows[0]['state_0d_occurrences']} != {0, 1}:
        raise ValueError('held-81 old 0D did not split at visit 94')
    paths = (Path(__file__), PRIOR, old.SOURCE,
             Path(old.__file__), Path(edge.__file__),
             Path(gate.__file__), Path(serial.__file__),
             RESULTS / 'joint-mask04-12a-visit94-old0d-expanded.json')
    report = dict(experiment='visit-94 replay of older passing answer stream with state 0D',
                  fixture=dict(carrier_offset=112, selector='60',
                               modes=['held_81', 'edge_81_A1'],
                               captured_visits=[46, 47, 93, 94, 141]),
                  cases=rows,
                  limitations=[
                      'The carrier, ADC, latch and mode paths remain assumed.',
                      'Two mode fixtures of the same payload are not independent data holdouts.',
                      'A differing visit-94 bit exposes timing variation but does not by itself identify physical logic.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print([(case['mode'], len(case['state_0d_occurrences']),
            len(case['candidate_wrong_indices'])) for case in report['cases']])
