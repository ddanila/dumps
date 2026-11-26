"""Control phase-131 carrier/payloads at the prior calibrated gain."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh
from joint_mask04_12a_mode_phase131_gain_challenge import MODEL, OFFSET, PAYLOADS
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-mode-phase131-baseline-control.json'


def run(out=OUT):
    with patch.object(fresh, 'MODEL', MODEL), \
            patch.object(fresh, 'PAYLOADS', PAYLOADS), \
            patch.object(fresh, 'OFFSET', OFFSET):
        report = fresh.run(out=out)
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    known = {int(code, 16) for code in model['trained_state_phase']}
    known.add(0x3D)
    for case in report['cases']:
        states = [sample_state(symbol, SELECTED)
                  for symbol in case['multi_visit_symbols']]
        phases = [circuit(state, 1) for state in states]
        decoded = [inverse[(right - left) & 3]
                   for left, right in zip(phases, phases[1:])]
        case['package_circuit_wrong_indices'] = [
            index for index, (got, want) in
            enumerate(zip(decoded, case['expected_dibits'][1:]), 1)
            if got != want]
        case['package_circuit_unseen_states'] = sorted(
            f'{value:02X}' for value in set(states) - known)
        if len(states) != 65 or len(decoded) != 64:
            raise ValueError(('baseline control symbol count changed',
                              case['selector']))
        print('baseline circuit', case['selector'],
              len(case['package_circuit_wrong_indices']),
              case['package_circuit_unseen_states'], flush=True)
    report['experiment'] = ('phase-131 carrier/payload control at original '
                            'calibrated line gain')
    report['fixture']['phase_model'] = MODEL.name
    report['fixture']['gain_factor'] = 1.0
    report['fixture']['package_circuit'] = 'photo_u15_u19_u21_phase_route.py'
    report['limitations'].append(
        'This control changes only receive gain relative to the phase-131 gain challenge; both retain assumed board and line routes.')
    for path in (Path(__file__),
                 HERE / 'joint_mask04_12a_mode_phase131_gain_challenge.py',
                 HERE / 'photo_u15_u19_u21_phase_route.py'):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
