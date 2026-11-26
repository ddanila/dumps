"""Challenge the frozen photographed-package phase circuit at changed gain."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from photo_u15_u19_u21_phase_route import circuit
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
GAIN = HERE / 'results/joint-mask04-12a-mode-phase131-gain-fixture.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase131-gain-challenge.json'
PAYLOADS = {
    '40': (0x2B, 0xC5, 0x70, 0x9E, 0x14, 0xF8, 0x63, 0xAD),
    '60': (0x91, 0x3F, 0xE4, 0x58, 0xC2, 0x06, 0x7B, 0xD0),
}
OFFSET = 131


def run(out=OUT):
    gain_fixture = json.loads(GAIN.read_text())
    if (gain_fixture['gain_factor'] != 1.25 or
            gain_fixture['source_sha256'] != hashlib.sha256(
                fresh.FIXED.read_bytes()).hexdigest()):
        raise ValueError('changed-gain fixture or source changed')
    with patch.object(fresh, 'MODEL', MODEL), \
            patch.object(fresh, 'FIXED', GAIN), \
            patch.object(fresh, 'PAYLOADS', PAYLOADS), \
            patch.object(fresh, 'OFFSET', OFFSET):
        report = fresh.run(out=out)
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    known = {int(code, 16) for code in model['trained_state_phase']}
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        if controller_sha != report['fixture']['controller_probe_sha256']:
            raise ValueError('controller binary changed between replays')
        with patch.object(serial, 'phase', lambda state, covers: circuit(state, 1)):
            for case in report['cases']:
                states = [sample_state(symbol, SELECTED)
                          for symbol in case['multi_visit_symbols']]
                phases = [circuit(state, 1) for state in states]
                decoded = [inverse[(after - before) & 3] for before, after in
                           zip(phases, phases[1:])]
                case['package_circuit_wrong_indices'] = [
                    index for index, (got, want) in
                    enumerate(zip(decoded, case['expected_dibits'][1:]), 1)
                    if got != want]
                case['package_circuit_phases'] = phases
                case['package_circuit_unseen_states'] = sorted(
                    f'{value:02X}' for value in set(states) - known)
                payload = [int(value, 16) for value in case['payload']]
                delay = 5 if case['selector'] == '40' else 18
                offered = line_octets(payload, delay)
                replay_case = dict(case, offered_line_bytes=[f'{x:02X}' for x in offered])
                score = serial.replay(replay_case, serial.VARIANTS['aligned'],
                                      None, inverse, exe)
                case['package_circuit_serial'] = score
                if len(states) != 65 or len(decoded) != 64:
                    raise ValueError(('phase-131 symbol count changed',
                                      case['selector']))
                print('package circuit', case['selector'],
                      'errors', len(case['package_circuit_wrong_indices']),
                      'unseen', case['package_circuit_unseen_states'],
                      'controller bytes', score['controller_decoded_bytes'], flush=True)
    report['experiment'] = ('frozen package phase circuit at carrier offset 131 '
                            'and 1.25x calibrated receive gain')
    report['fixture']['phase_model'] = MODEL.name
    report['fixture']['gain_factor'] = 1.25
    report['fixture']['gain_fixture'] = GAIN.name
    report['fixture']['package_circuit'] = 'photo_u15_u19_u21_phase_route.py'
    report['limitations'].append(
        'Carrier offset, payloads and gain are new; the package circuit and mode mapping are frozen. Physical nets are still assumed.')
    for path in (Path(__file__), GAIN,
                 HERE / 'photo_u15_u19_u21_phase_route.py',
                 HERE / 'joint_mask04_12a_row0_serial_timing.py'):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
