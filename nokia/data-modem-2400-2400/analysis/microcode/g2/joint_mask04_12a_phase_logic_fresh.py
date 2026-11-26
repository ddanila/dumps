"""Fresh-payload and carrier-start challenge of frozen receive phase logic."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_phase_boolean import phase
from joint_mask04_12a_phase_potential import EXTRAS
from joint_mask04_12a_sixth_receive_bit import state
from joint_mask04_tx_12a_delayed_latch import capturing_execute

HERE = Path(__file__).resolve().parent
LOGIC = HERE / 'results/joint-mask04-12a-phase-boolean.json'
POTENTIAL = HERE / 'results/joint-mask04-12a-phase-potential.json'
PAYLOADS = {'40': (0x53, 0xA1, 0x0C, 0xF7, 0x2D, 0x84, 0xB9, 0x6E),
            '60': (0xC4, 0x37, 0x9A, 0x05, 0xE2, 0x71, 0x8F, 0xD0)}
OFFSETS = (16, 80)


def run():
    logic = json.loads(LOGIC.read_text())
    potential = json.loads(POTENTIAL.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in logic['phase_bits']]
    convention = tuple(logic['fixture']['phase_convention'])
    inverse = {step: dibit for dibit, step in enumerate(convention)}
    developed = {int(key, 16) for key in potential['state_phase']}
    with tempfile.TemporaryDirectory() as temporary:
        controller, controller_sha = handoff.compiled_controller(temporary)
        for offset in OFFSETS:
            def selected_execute(pair):
                if pair != (frozen.PHASE_VISIT, 32):
                    raise ValueError(f'unexpected original phase fixture: {pair}')
                return capturing_execute((pair[0], offset))

            out = HERE / f'results/joint-mask04-12a-phase-logic-fresh-{offset}.json'
            with patch.object(frozen, 'PAYLOADS', PAYLOADS), \
                    patch.object(frozen, 'LEVELS', (1.0,)), \
                    patch.object(frozen, 'capturing_execute', selected_execute):
                report = frozen.run(out=out)
            report['experiment'] = f'frozen six-bit phase logic on fresh payloads at R1 offset {offset}'
            report['fixture']['phase_offset'] = offset
            report['fixture']['phase_logic'] = 'separately minimized Boolean phase bits and frozen DPSK difference'
            report['fixture']['phase_logic_controller_sha256'] = controller_sha
            for case in report['cases']:
                states = [state(a, b, EXTRAS)
                          for a, b in zip(case['first_y'], case['second_y'])]
                decoded = [None] + [inverse[(phase(after, covers) -
                                             phase(before, covers)) % 4]
                                    for before, after in zip(states, states[1:])]
                wrong = [i for i, (got, want) in enumerate(
                    zip(decoded[1:], case['expected_dibits'][1:]), 1)
                         if got != want]
                selector = case['selector']
                delay = 5 if selector == '40' else 18
                offered = [int(value, 16) for value in case['offered_line_bytes']]
                readout = line.readout_result(decoded, case['expected_dibits'],
                                              offered, controller, selector, delay)
                case['phase_logic'] = dict(
                    six_bit_states=[f'{value:02X}' for value in states],
                    new_states=sorted(f'{value:02X}' for value in set(states)
                                      if value not in developed),
                    decoded_dibits=decoded,
                    wrong_indices=wrong,
                    lookup_agrees=decoded == case['decoded_dibits'],
                    readout=readout)
                print('logic', offset, selector, 'wrong', len(wrong),
                      'new states', case['phase_logic']['new_states'], flush=True)
            report['limitations'].extend([
                'The new payloads and carrier offsets were fixed before observing these receiver outcomes.',
                'The Boolean outputs for states absent from development are minimization extrapolations, not measured circuit behavior.',
            ])
            for path in (Path(__file__), LOGIC, POTENTIAL,
                         HERE / 'joint_mask04_12a_phase_boolean.py'):
                report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
                    hashlib.sha256(path.read_bytes()).hexdigest())
            out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
