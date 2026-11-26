"""Preserve multi-visit Y and row bytes for the gain-collision witness."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_fifth_receive_bit as fifth

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-fifth-receive-bit.json'
OUT = HERE / 'results/joint-mask04-12a-third-capture-low-gain.json'
PHASES = ('46', '47', '93', '94', '141')


def run(out=OUT):
    captured = []
    original_capture = fifth.loopback.capture

    def preserving_capture(*args, **kwargs):
        result, adc, symbols = original_capture(*args, **kwargs)
        if len(symbols) != 65 or tuple(symbols[0]['visits']) != PHASES:
            raise ValueError('receive visit capture fixture changed')
        captured.append(symbols)
        return result, adc, symbols

    with patch.object(fifth, 'LEVELS', (0.75,)), \
            patch.object(fifth.loopback, 'capture', preserving_capture):
        report = fifth.run(out=out)
    previous = json.loads(PRIOR.read_text())
    old_cases = [case for case in previous['cases']
                 if case['fixture'] in ('level0.75', 'half_fresh')]
    if len(captured) != len(report['cases']) or len(report['cases']) != len(old_cases):
        raise ValueError('receive capture count changed')
    report['experiment'] = 'full multi-visit receive capture for 75% gain collisions'
    report['fixture']['captured_visits'] = PHASES
    for case, old, symbols in zip(report['cases'], old_cases, captured):
        for key in ('fixture', 'selector', 'rx_trace_digest',
                    'adc_sha256', 'expected_dibits', 'first_y', 'second_y'):
            if case[key] != old[key]:
                raise ValueError(f'previous gain witness changed: {key}')
        if ([s['visits']['46']['y3f8'] for s in symbols] != case['first_y'] or
                [s['visits']['93']['y3f8'] for s in symbols] != case['second_y']):
            raise ValueError('original Y capture changed')
        case['multi_visit_symbols'] = symbols
        print('gain captured', case['fixture'], case['selector'], len(symbols), flush=True)
    report['limitations'].append(
        'These five PROM visit phases are emulator capture points, not identified Nokia latch edges.')
    for path in (Path(__file__), PRIOR):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
