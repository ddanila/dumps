"""Frozen row-phase gate challenge on new payloads across fixed line levels."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, sample_state
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_tx_12a_delayed_latch import capturing_execute

LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean.json'
OUT = HERE / 'results/joint-mask04-12a-row0-boolean-gain.json'
PAYLOADS = {'40': (0x07, 0xB2, 0x59, 0xEC, 0x31, 0x8D, 0xC4, 0x6A),
            '60': (0xF1, 0x26, 0x90, 0x4B, 0xDA, 0x73, 0x05, 0xBE)}
LEVELS = (0.75, 1.0, 1.25)
OFFSET = 24


def run(out=OUT):
    model = json.loads(LOGIC.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in model['phase_bits']]
    inverse = {step: dibit for dibit, step in enumerate(
        model['fixture']['phase_convention'])}
    known = set(model['state_phase'])
    captured = []
    original_capture = frozen.loopback.capture

    def selected_execute(pair):
        if pair != (frozen.PHASE_VISIT, 32):
            raise ValueError(f'unexpected original phase fixture: {pair}')
        return capturing_execute((pair[0], OFFSET))

    def preserving_capture(*args, **kwargs):
        result, adc, symbols = original_capture(*args, **kwargs)
        if len(symbols) != 65 or '46' not in symbols[0]['visits']:
            raise ValueError('receive visit capture fixture changed')
        captured.append(symbols)
        return result, adc, symbols

    with patch.object(frozen, 'PAYLOADS', PAYLOADS), \
            patch.object(frozen, 'LEVELS', LEVELS), \
            patch.object(frozen, 'capturing_execute', selected_execute), \
            patch.object(frozen.loopback, 'capture', preserving_capture):
        report = frozen.run(out=out)
    if len(report['cases']) != len(captured) or len(captured) != 6:
        raise ValueError('gain receive capture count changed')
    report['experiment'] = 'frozen row-0 Boolean phase gates on new payloads across gain'
    report['fixture']['phase_offset'] = OFFSET
    report['fixture']['row_phase_feature'] = SELECTED
    with tempfile.TemporaryDirectory() as temporary:
        controller, controller_sha = handoff.compiled_controller(temporary)
        report['fixture']['boolean_phase_controller_sha256'] = controller_sha
        for case, symbols in zip(report['cases'], captured):
            if ([s['visits']['46']['y3f8'] for s in symbols] != case['first_y'] or
                    [s['visits']['93']['y3f8'] for s in symbols] != case['second_y']):
                raise ValueError('original Y capture changed')
            values = [sample_state(symbol, SELECTED) for symbol in symbols]
            decoded = [None] + [inverse[(phase(after, covers) -
                                         phase(before, covers)) % 4]
                                for before, after in zip(values, values[1:])]
            wrong = [i for i, (got, want) in enumerate(
                zip(decoded[1:], case['expected_dibits'][1:]), 1)
                     if got != want]
            selector = case['selector']
            delay = 5 if selector == '40' else 18
            offered = [int(value, 16) for value in case['offered_line_bytes']]
            case['multi_visit_symbols'] = symbols
            case['boolean_phase'] = dict(
                states=[f'{value:02X}' for value in values],
                new_states=sorted(f'{value:02X}' for value in set(values)
                                  if f'{value:02X}' not in known),
                decoded_dibits=decoded, wrong_indices=wrong,
                readout=line.readout_result(decoded, case['expected_dibits'],
                                            offered, controller, selector, delay))
            print('gain', selector, case['level'], 'wrong', len(wrong),
                  'new', case['boolean_phase']['new_states'], flush=True)
    report['limitations'].extend([
        'The gate feature and Boolean truth table were frozen before these payloads and gain levels.',
        'The offset, analog gain, ADC schedule, row latch and serial connections are diagnostic assumptions.',
    ])
    for path in (Path(__file__), LOGIC,
                 HERE / 'joint_mask04_12a_row0_boolean.py',
                 HERE / 'joint_mask04_12a_multivisit_phase_screen.py'):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
