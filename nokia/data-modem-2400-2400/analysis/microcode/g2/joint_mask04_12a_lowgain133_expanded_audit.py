"""Measure whether adjacent capture values distinguish the failed phase state."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase

HERE = Path(__file__).resolve().parent
RUN = HERE / 'results/joint-mask04-12a-lowgain133-expanded-visits.json'
OUT = HERE / 'results/joint-mask04-12a-lowgain133-expanded-audit.json'


def run(out=OUT):
    saved = json.loads(RUN.read_text())
    targets = []
    positives = []
    for case in saved['cases']:
        for symbol in case['multi_visit_symbols']:
            code = sample_state(symbol, SELECTED)
            if code == 0x1D:
                targets.append(symbol)
            elif corrected_phase(code, 1) & 1:
                positives.append(symbol)
    if len(targets) != 6:
        raise ValueError('failed-state count changed')
    fields = {}
    for visit in ('46', '47', '93', '94', '141'):
        for site in ('row0', 'y3f8'):
            target = Counter(symbol['visits'][visit][site]
                             for symbol in targets)
            other = Counter(symbol['visits'][visit][site]
                            for symbol in positives)
            fields[f'{visit}/{site}'] = dict(
                target_values={f'{value:02X}': count
                               for value, count in sorted(target.items())},
                opposite_phase_bit_values={f'{value:02X}': count
                                           for value, count in sorted(other.items())},
                exact_value_overlap={f'{value:02X}': other[value]
                                     for value in target if other[value]})
    if (fields['94/y3f8']['target_values'] != {'4F': 6} or
            fields['141/row0']['exact_value_overlap'] != {'9F': 24} or
            fields['141/y3f8']['target_values'] != {'3F': 4, '4F': 2}):
        raise ValueError('adjacent-visit signature changed')
    paths = (Path(__file__), RUN,
             HERE / 'joint_mask04_12a_lowgain133_expanded_visits.py',
             HERE / 'joint_mask04_12a_phasebit0_veto.py')
    report = dict(experiment='adjacent-visit signature of unseen state 1D',
                  fixture=dict(carrier_offset=133, gain_factor=0.8,
                               selectors=['40', '60'], target_count=len(targets),
                               opposite_phase_bit_symbols=len(positives)),
                  fields=fields,
                  limitations=[
                      'These are emulator capture values under an assumed ADC and clock; no physical latch edge is identified.',
                      'The opposite-bit comparison covers this low-gain fixture, not all saved mode-1 labels.',
                      'A unique byte in this capture is not a validated physical discriminator or a new receiver circuit.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print(report['fixture'])
