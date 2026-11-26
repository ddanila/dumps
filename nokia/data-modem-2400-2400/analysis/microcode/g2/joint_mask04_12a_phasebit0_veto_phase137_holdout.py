"""Challenge frozen phase-bit-0 veto on new real-PROM mode streams."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase
from photo_joint_line_filter_screen import SILENCE_END
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
GRAPH = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'
GAIN = RESULTS / 'joint-mask04-12a-mode-phase137-gain-fixture.json'
ORIGINAL_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
OUT = RESULTS / 'joint-mask04-12a-phasebit0-veto-phase137-holdout.json'
PAYLOADS = {
    '40': (0xE2, 0x5B, 0x91, 0x0F, 0xC7, 0x34, 0xAD, 0x68),
    '60': (0x76, 0xD1, 0x08, 0xB5, 0x2A, 0xEC, 0x43, 0x9F),
}
OFFSET = 137
FACTOR = 1.15
SHIFT = 5


def run(out=OUT):
    gain_fixture = json.loads(GAIN.read_text())
    if (gain_fixture['gain_factor'] != FACTOR or
            gain_fixture['source_sha256'] != hashlib.sha256(
                ORIGINAL_GAIN.read_bytes()).hexdigest()):
        raise ValueError('holdout gain fixture changed')
    waves = []
    original_bandpass = fresh.bandpass
    def capture_bandpass(samples, q):
        result = original_bandpass(samples, q)
        waves.append(result)
        return result
    with patch.object(fresh, 'MODEL', MODEL), \
            patch.object(fresh, 'FIXED', GAIN), \
            patch.object(fresh, 'PAYLOADS', PAYLOADS), \
            patch.object(fresh, 'OFFSET', OFFSET), \
            patch.object(fresh, 'bandpass', capture_bandpass):
        report = fresh.run(out=out)
    if len(waves) != 2:
        raise ValueError('holdout line capture count changed')
    model = json.loads(MODEL.read_text())
    graph = json.loads(GRAPH.read_text())
    known = {int(code, 16) for code in graph['combined_mode81_phase_labels']}
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        if controller_sha != report['fixture']['controller_probe_sha256']:
            raise ValueError('controller binary changed between replays')
        with patch.object(serial, 'phase', lambda state, covers:
                          corrected_phase(state, 1)):
            for case, wave in zip(report['cases'], waves):
                states = [sample_state(symbol, SELECTED)
                          for symbol in case['multi_visit_symbols']]
                phases = [corrected_phase(state, 1) for state in states]
                case['corrected_wrong_indices'] = [
                    index for index in range(1, len(phases))
                    if inverse[(phases[index] - phases[index - 1]) & 3]
                    != case['expected_dibits'][index]]
                case['corrected_phases'] = phases
                case['unseen_vs_20_labels'] = sorted(
                    f'{state:02X}' for state in set(states) - known)
                gain = next(bus['gain'] for bus in next(
                    item for item in gain_fixture['cases']
                    if item['selector'] == case['selector'])['bus_cases']
                    if bus['bus_index'] == 0)
                selected = wave[SILENCE_END + SHIFT:
                                SILENCE_END + SHIFT + handoff.RX_SYMBOLS * 8]
                unbounded = [round(value * gain) for value in selected]
                pcm = [max(-127, min(127, value)) for value in unbounded]
                if hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != case['pcm_sha256']:
                    raise ValueError(('holdout PCM changed', case['selector']))
                case['clipped_samples'] = sum(abs(value) > 127
                                              for value in unbounded)
                payload = [int(value, 16) for value in case['payload']]
                delay = 5 if case['selector'] == '40' else 18
                offered = line_octets(payload, delay)
                replay_case = dict(case,
                                   offered_line_bytes=[f'{x:02X}' for x in offered])
                score = serial.replay(replay_case, serial.VARIANTS['aligned'],
                                      None, inverse, exe)
                case['corrected_serial'] = score
                if (len(states) != 65 or len(case['expected_dibits']) != 65 or
                        score['wrong_decision_indices'] != case['corrected_wrong_indices']):
                    raise ValueError(('holdout replay mismatch', case['selector']))
                print('veto holdout', case['selector'],
                      'reference', len(case['reference_wrong_indices']),
                      'old', len(case['frozen_gate_wrong_indices']),
                      'veto', len(case['corrected_wrong_indices']),
                      'unseen', case['unseen_vs_20_labels'],
                      'clipped', case['clipped_samples'],
                      'bytes', score['recovered_matches_offered'], flush=True)
    report['experiment'] = ('frozen phase-bit-0 veto at carrier offset 137, '
                            'new payloads and 1.15x receive gain')
    report['fixture']['phase_model'] = MODEL.name
    report['fixture']['correction'] = 'joint_mask04_12a_phasebit0_veto.py'
    report['fixture']['gain_factor'] = FACTOR
    report['fixture']['gain_fixture'] = GAIN.name
    report['limitations'].append(
        'The two veto terms are frozen from prior runs. No physical gate package or mode/serial connection is identified for them.')
    for path in (Path(__file__), GAIN, GRAPH, ORIGINAL_GAIN,
                 HERE / 'joint_mask04_12a_phasebit0_veto.py',
                 HERE / 'joint_mask04_12a_row0_serial_timing.py'):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
