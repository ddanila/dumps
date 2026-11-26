"""Challenge frozen mode-aware gates and the package circuit at phase 125."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from photo_u15_u19_u21_phase_route import circuit
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase125-challenge.json'
PAYLOADS = {
    '40': (0xD6, 0x31, 0x8C, 0x05, 0xE9, 0x72, 0x4B, 0xAF),
    '60': (0x49, 0xF0, 0x26, 0xBD, 0x83, 0x1C, 0xE7, 0x5A),
}
OFFSET = 125


def run(out=OUT):
    with patch.object(fresh, 'MODEL', MODEL), \
            patch.object(fresh, 'PAYLOADS', PAYLOADS), \
            patch.object(fresh, 'OFFSET', OFFSET):
        report = fresh.run(out=out)
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        if controller_sha != report['fixture']['controller_probe_sha256']:
            raise ValueError('controller binary changed between replays')
        with patch.object(serial, 'phase', lambda state, covers: circuit(state, 1)):
            for case in report['cases']:
                states = [sample_state(symbol, SELECTED)
                          for symbol in case['multi_visit_symbols']]
                phases = [circuit(state, 1) for state in states]
                decoded = [inverse[(right - left) & 3] for left, right in
                           zip(phases, phases[1:])]
                case['package_circuit_wrong_indices'] = [
                    index for index, (got, want) in
                    enumerate(zip(decoded, case['expected_dibits'][1:]), 1)
                    if got != want]
                case['package_circuit_phases'] = phases
                payload = [int(value, 16) for value in case['payload']]
                delay = 5 if case['selector'] == '40' else 18
                offered = line_octets(payload, delay)
                replay_case = dict(case, offered_line_bytes=[f'{x:02X}' for x in offered])
                score = serial.replay(replay_case, serial.VARIANTS['aligned'],
                                      None, inverse, exe)
                case['package_circuit_serial'] = score
                if (len(states) != 65 or len(decoded) != 64 or
                        case['package_circuit_wrong_indices'] or
                        score['wrong_decision_indices'] or
                        score['unknown_rxc_edges'] or
                        not score['recovered_matches_offered'] or
                        score['controller_decoded_bytes'] != payload or
                        score['controller_errors'] or score['controller_overruns']):
                    raise ValueError(('phase-125 package serial replay failed',
                                      case['selector'], score))
                print('package circuit', case['selector'], 'errors',
                      len(case['package_circuit_wrong_indices']),
                      'controller bytes', len(score['controller_decoded_bytes']))
    report['experiment'] = ('frozen package-budgeted phase circuit on fresh '
                            'phase-125 real-PROM controller streams')
    report['fixture']['phase_model'] = MODEL.name
    report['fixture']['package_circuit'] = 'photo_u15_u19_u21_phase_route.py'
    report['limitations'].append(
        'The package circuit is frozen from 34 prior labels; offset 125 and both payloads are new. Physical nets remain untraced.')
    for path in (Path(__file__), HERE / 'photo_u15_u19_u21_phase_route.py',
                 HERE / 'joint_mask04_12a_row0_serial_timing.py'):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
