"""Untouched payload and carrier-start holdout for two seven-bit phase states."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_seventh_phase_bit import HERE, states
from joint_mask04_tx_12a_delayed_latch import capturing_execute

SCREEN = HERE / 'results/joint-mask04-12a-seventh-phase-bit.json'
PAYLOADS = {'40': (0x21, 0x6D, 0xB8, 0x04, 0xF3, 0x9A, 0x57, 0xCE),
            '60': (0xD2, 0x08, 0x73, 0xA5, 0x4F, 0xC1, 0x96, 0x3B)}
OFFSETS = (48, 112)


def classify(case, candidate, controller):
    extra = tuple(candidate['extra'])
    potentials = {int(key, 16): value
                  for key, value in candidate['state_phase'].items()}
    component = {int(key, 16): index
                 for index, group in enumerate(candidate['component_states'])
                 for key in group}
    inverse = {step: dibit
               for dibit, step in enumerate(candidate['convention'])}
    samples = states(case, extra)
    decoded = [None]
    cross = []
    for index, (before, after) in enumerate(zip(samples, samples[1:]), 1):
        if before not in potentials or after not in potentials:
            decoded.append(None)
        elif component[before] != component[after]:
            decoded.append(None)
            cross.append(index)
        else:
            decoded.append(inverse[(potentials[after] - potentials[before]) % 4])
    wrong = [i for i, (got, want) in enumerate(
        zip(decoded[1:], case['expected_dibits'][1:]), 1)
             if got is not None and got != want]
    unknown = [i for i, got in enumerate(decoded[1:], 1) if got is None]
    selector = case['selector']
    delay = 5 if selector == '40' else 18
    offered = [int(value, 16) for value in case['offered_line_bytes']]
    return dict(extra=extra, observed_states=sorted(f'{value:02X}'
                                                    for value in set(samples)),
                new_states=sorted(f'{value:02X}' for value in set(samples)
                                  if value not in potentials),
                cross_component_indices=cross,
                decoded_dibits=decoded, wrong_indices=wrong,
                unknown_indices=unknown,
                readout=line.readout_result(decoded, case['expected_dibits'],
                                            offered, controller, selector, delay))


def run():
    candidates = json.loads(SCREEN.read_text())['survivors']
    if {tuple(row['extra']) for row in candidates} != {
            ('first', 4), ('second', 5)}:
        raise ValueError('seven-bit candidates changed')
    with tempfile.TemporaryDirectory() as temporary:
        controller, controller_sha = handoff.compiled_controller(temporary)
        for offset in OFFSETS:
            def selected_execute(pair):
                if pair != (frozen.PHASE_VISIT, 32):
                    raise ValueError(f'unexpected original phase fixture: {pair}')
                return capturing_execute((pair[0], offset))

            out = HERE / f'results/joint-mask04-12a-seventh-phase-fresh-{offset}.json'
            with patch.object(frozen, 'PAYLOADS', PAYLOADS), \
                    patch.object(frozen, 'LEVELS', (1.0,)), \
                    patch.object(frozen, 'capturing_execute', selected_execute):
                report = frozen.run(out=out)
            report['experiment'] = f'frozen seven-bit phase candidates on new payloads at R1 offset {offset}'
            report['fixture']['phase_offset'] = offset
            report['fixture']['seven_bit_candidates'] = [row['extra'] for row in candidates]
            report['fixture']['candidate_controller_sha256'] = controller_sha
            for case in report['cases']:
                case['seventh_phase'] = {
                    f"{row['extra'][0]}{row['extra'][1]}": classify(case, row, controller)
                    for row in candidates}
                print('seven-bit', offset, case['selector'],
                      [(name, len(value['wrong_indices']),
                        len(value['unknown_indices']))
                       for name, value in case['seventh_phase'].items()], flush=True)
            report['limitations'].extend([
                'The two seven-bit phase maps were frozen before these payloads and R1 offsets.',
                'A transition across disconnected development components or through an unseen state is undecided, not fitted here.',
            ])
            for path in (Path(__file__), SCREEN,
                         HERE / 'joint_mask04_12a_seventh_phase_bit.py'):
                report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
                    hashlib.sha256(path.read_bytes()).hexdigest())
            out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
