"""Preserve all existing multi-visit PROM receive captures on failed phase starts."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_12a_phase_logic_fresh as fresh
from joint_mask04_tx_12a_delayed_latch import capturing_execute

HERE = Path(__file__).resolve().parent
PHASES = ('46', '47', '93', '94', '141')


def run():
    original_capture = frozen.loopback.capture
    for offset in fresh.OFFSETS:
        captured = []

        def selected_execute(pair):
            if pair != (frozen.PHASE_VISIT, 32):
                raise ValueError(f'unexpected original phase fixture: {pair}')
            return capturing_execute((pair[0], offset))

        def preserving_capture(*args, **kwargs):
            result, adc, symbols = original_capture(*args, **kwargs)
            if len(symbols) != 65 or tuple(symbols[0]['visits']) != PHASES:
                raise ValueError('receive visit capture fixture changed')
            captured.append(symbols)
            return result, adc, symbols

        out = HERE / f'results/joint-mask04-12a-third-capture-{offset}.json'
        previous = json.loads((HERE / f'results/joint-mask04-12a-phase-logic-fresh-{offset}.json').read_text())
        with patch.object(frozen, 'PAYLOADS', fresh.PAYLOADS), \
                patch.object(frozen, 'LEVELS', (1.0,)), \
                patch.object(frozen, 'capturing_execute', selected_execute), \
                patch.object(frozen.loopback, 'capture', preserving_capture):
            report = frozen.run(out=out)
        if len(captured) != len(report['cases']) or len(report['cases']) != len(previous['cases']):
            raise ValueError('receive capture count changed')
        report['experiment'] = f'full multi-visit receive capture at R1 offset {offset}'
        report['fixture']['phase_offset'] = offset
        report['fixture']['captured_visits'] = PHASES
        for case, old, symbols in zip(report['cases'], previous['cases'], captured):
            for key in ('selector', 'tx_trace_digest', 'rx_trace_digest',
                        'raw_sha256', 'pcm_sha256', 'adc_sha256', 'expected_dibits'):
                if case[key] != old[key]:
                    raise ValueError(f'previous offset-{offset} trace changed: {key}')
            if ([s['visits']['46']['y3f8'] for s in symbols] != case['first_y'] or
                    [s['visits']['93']['y3f8'] for s in symbols] != case['second_y']):
                raise ValueError('original Y capture changed')
            case['multi_visit_symbols'] = symbols
            print('captured', offset, case['selector'], len(symbols), flush=True)
        report['limitations'].append(
            'These five PROM visit phases are emulator capture points, not identified Nokia latch edges.')
        for path in (Path(__file__),
                     HERE / f'results/joint-mask04-12a-phase-logic-fresh-{offset}.json',
                     HERE / 'joint_mask04_12a_phase_logic_fresh.py'):
            report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
                hashlib.sha256(path.read_bytes()).hexdigest())
        out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
