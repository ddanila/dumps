"""New-payload carrier-start challenge for frozen row-0 Boolean phase gates."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_row0_fresh as row0
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_row0_boolean import HERE, phase

LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean.json'
PAYLOADS = {'40': (0x8C, 0x13, 0xE7, 0x5A, 0x20, 0xD9, 0x46, 0xBF),
            '60': (0x31, 0xC6, 0x0B, 0xF4, 0xA8, 0x57, 0xDE, 0x92)}
OFFSETS = (24, 88)


def run():
    model = json.loads(LOGIC.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in model['phase_bits']]
    inverse = {step: dibit for dibit, step in enumerate(
        model['fixture']['phase_convention'])}
    known = set(model['state_phase'])
    with patch.object(row0, 'PAYLOADS', PAYLOADS), \
            patch.object(row0, 'OFFSETS', OFFSETS):
        row0.run()
    with tempfile.TemporaryDirectory() as temporary:
        controller, controller_sha = handoff.compiled_controller(temporary)
        for offset in OFFSETS:
            out = HERE / f'results/joint-mask04-12a-row0-fresh-{offset}.json'
            report = json.loads(out.read_text())
            report['experiment'] = f'frozen row-0 Boolean phase gates on new payloads at R1 offset {offset}'
            report['fixture']['boolean_phase_controller_sha256'] = controller_sha
            for case in report['cases']:
                values = [int(value, 16) for value in case['row_phase']['states']]
                decoded = [None] + [inverse[(phase(after, covers) -
                                             phase(before, covers)) % 4]
                                    for before, after in zip(values, values[1:])]
                wrong = [i for i, (got, want) in enumerate(
                    zip(decoded[1:], case['expected_dibits'][1:]), 1)
                         if got != want]
                selector = case['selector']
                delay = 5 if selector == '40' else 18
                offered = [int(value, 16) for value in case['offered_line_bytes']]
                case['boolean_phase'] = dict(
                    states=case['row_phase']['states'],
                    new_states=sorted(f'{value:02X}' for value in set(values)
                                      if f'{value:02X}' not in known),
                    decoded_dibits=decoded, wrong_indices=wrong,
                    readout=line.readout_result(decoded, case['expected_dibits'],
                                                offered, controller, selector, delay))
                print('Boolean row0', offset, selector, 'wrong', len(wrong),
                      'new states', case['boolean_phase']['new_states'], flush=True)
            report['limitations'].extend([
                'The two-output Boolean gates were frozen before these payloads and offsets.',
                'Outputs on states absent from development are gate extrapolations, not measured Nokia logic.',
            ])
            for path in (Path(__file__), LOGIC,
                         HERE / 'joint_mask04_12a_row0_boolean.py'):
                report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
                    hashlib.sha256(path.read_bytes()).hexdigest())
            out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
