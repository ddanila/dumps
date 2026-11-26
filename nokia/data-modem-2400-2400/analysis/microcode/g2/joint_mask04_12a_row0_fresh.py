"""Challenge the frozen 3ED-row0 receive phase bit on new real-PROM streams."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, sample_state
from joint_mask04_tx_12a_delayed_latch import capturing_execute

SCREEN = HERE / 'results/joint-mask04-12a-multivisit-phase-screen.json'
PAYLOADS = {'40': (0x4A, 0xD7, 0x1B, 0x90, 0xE5, 0x3C, 0x62, 0xAF),
            '60': (0xB3, 0x0E, 0x75, 0xC8, 0x29, 0xF4, 0x81, 0x5D)}
OFFSETS = (0, 64)


def run():
    selected = json.loads(SCREEN.read_text())['selected']
    if tuple(selected['feature']) != SELECTED or selected['component_sizes'] != [11]:
        raise ValueError('frozen row-0 phase fixture changed')
    potentials = {int(key, 16): value for key, value in selected['state_phase'].items()}
    inverse = {step: dibit
               for dibit, step in enumerate(selected['best_convention'])}
    original_capture = frozen.loopback.capture
    with tempfile.TemporaryDirectory() as temporary:
        controller, controller_sha = handoff.compiled_controller(temporary)
        for offset in OFFSETS:
            captured = []

            def selected_execute(pair):
                if pair != (frozen.PHASE_VISIT, 32):
                    raise ValueError(f'unexpected original phase fixture: {pair}')
                return capturing_execute((pair[0], offset))

            def preserving_capture(*args, **kwargs):
                result, adc, symbols = original_capture(*args, **kwargs)
                if len(symbols) != 65 or '46' not in symbols[0]['visits']:
                    raise ValueError('receive visit capture fixture changed')
                captured.append(symbols)
                return result, adc, symbols

            out = HERE / f'results/joint-mask04-12a-row0-fresh-{offset}.json'
            with patch.object(frozen, 'PAYLOADS', PAYLOADS), \
                    patch.object(frozen, 'LEVELS', (1.0,)), \
                    patch.object(frozen, 'capturing_execute', selected_execute), \
                    patch.object(frozen.loopback, 'capture', preserving_capture):
                report = frozen.run(out=out)
            if len(report['cases']) != len(captured) or len(captured) != 2:
                raise ValueError('fresh receive capture count changed')
            report['experiment'] = f'frozen 3ED row-0 bit 0 phase readout on new payloads at R1 offset {offset}'
            report['fixture']['phase_offset'] = offset
            report['fixture']['row_phase_feature'] = SELECTED
            report['fixture']['row_phase_controller_sha256'] = controller_sha
            for case, symbols in zip(report['cases'], captured):
                if ([s['visits']['46']['y3f8'] for s in symbols] != case['first_y'] or
                        [s['visits']['93']['y3f8'] for s in symbols] != case['second_y']):
                    raise ValueError('baseline Y capture changed')
                states = [sample_state(symbol, SELECTED) for symbol in symbols]
                decoded = [None] + [None if before not in potentials
                                    or after not in potentials
                                    else inverse[(potentials[after] -
                                                  potentials[before]) % 4]
                                    for before, after in zip(states, states[1:])]
                wrong = [i for i, (got, want) in enumerate(
                    zip(decoded[1:], case['expected_dibits'][1:]), 1)
                         if got is not None and got != want]
                unknown = [i for i, got in enumerate(decoded[1:], 1)
                           if got is None]
                selector = case['selector']
                delay = 5 if selector == '40' else 18
                offered = [int(value, 16) for value in case['offered_line_bytes']]
                case['multi_visit_symbols'] = symbols
                case['row_phase'] = dict(
                    states=[f'{value:02X}' for value in states],
                    new_states=sorted(f'{value:02X}' for value in set(states)
                                      if value not in potentials),
                    decoded_dibits=decoded, wrong_indices=wrong,
                    unknown_indices=unknown,
                    readout=line.readout_result(decoded, case['expected_dibits'],
                                                offered, controller, selector, delay))
                print('row0', offset, selector, 'wrong', len(wrong),
                      'unknown', len(unknown), 'new', case['row_phase']['new_states'],
                      flush=True)
            report['limitations'].extend([
                'The row-0 bit, phase map and dibit convention were frozen before these payloads and offsets.',
                'The 3ED row-0 output is an executed internal signal; its external latch and USART route are untraced.',
            ])
            for path in (Path(__file__), SCREEN,
                         HERE / 'joint_mask04_12a_multivisit_phase_screen.py'):
                report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
                    hashlib.sha256(path.read_bytes()).hexdigest())
            out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
