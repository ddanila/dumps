"""Freeze the offset-177 diagnosis as a revised mode-bit phase cover."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_modebit66_cover import (
    FEATURES, STEPS, gate_phase as old_gate_phase,
)

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
DIAGNOSIS = RESULTS / 'joint-mask04-12a-modebit66-diagnosis.json'
OUT = RESULTS / 'joint-mask04-12a-modebit70-revision.json'
CORRECTED_STATE = 0x32D


def gate_phase(state):
    return old_gate_phase(state) | int(state == CORRECTED_STATE)


def run(out=OUT):
    diagnosis = json.loads(DIAGNOSIS.read_text())
    graph = diagnosis['joined_graph']
    if ((graph['state_codes'], graph['components'],
         graph['directed_conflicts']) != (64, [64], 0) or
            diagnosis['new_state_desired_labels'] !=
            {'0C2': 1, '32D': 3, '336': 2}):
        raise ValueError('development diagnosis changed')
    wrong = [key for key, phase in graph['relative_phase'].items()
             if gate_phase(int(key, 16)) != ((phase + 1) & 3)]
    if wrong:
        raise ValueError(('revised cover mismatches development graph', wrong))
    sources = (Path(__file__), DIAGNOSIS,
               HERE / 'joint_mask04_12a_modebit66_cover.py')
    report = dict(experiment='frozen 70-stream mode-bit phase cover revision',
                  fixture=dict(development_streams=70, observed_states=64,
                               phase_convention=STEPS, features=FEATURES,
                               global_phase_offset=1,
                               corrected_state=f'{CORRECTED_STATE:03X}'),
                  mode_bit_graph=graph,
                  development_label_mismatches=wrong,
                  correction='OR phase bit 0 with exact state 32D',
                  limitations=[
                      'The offset-177 cases are development data, not validation of this revision.',
                      'The extra exact-state term is a Boolean correction, not a photographed-package circuit.',
                      'Mode, analog, latch and serial connections remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('states', result['fixture']['observed_states'],
          'development mismatches', len(result['development_label_mismatches']))
