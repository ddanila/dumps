"""Test controller-frame byte candidates after one real-PROM vector to 133."""

import hashlib
from collections import Counter
from pathlib import Path

from board_enable_takeover import candidate_board
from board_vector_screen import at_wait, screen_one

HERE = Path(__file__).resolve().parent
from board_vector_screen import BOARD, ASSUMED
from photo_hypotheses import scenario
from common import save

VECTOR = 0x111
TARGET = 0x133
FRAME_BYTES = (0x80, 0x02, 0x81, 0x7A, 0xC0, 0x42, 0x22, 0xEA)
INPUT_BYTES = (0, *FRAME_BYTES, 0xFF)


def run(out=HERE / 'results/board-vector-input.json'):
    board = candidate_board()
    fixture = scenario(0)
    fixture['initial_inputs'].update(takeover=0, drive=0, address=0)
    cases = []
    wait_cycles = {}
    for seed_name, seed in (('unknown', None), ('zero', 0), ('ones', 15)):
        wait_cycle, wait_engine = at_wait(board, fixture, seed)
        wait_cycles[seed_name] = wait_cycle
        for test in (0, 1):
            for data in INPUT_BYTES:
                case, _ = screen_one(wait_engine, fixture, VECTOR, TARGET,
                                     {'test': test, 'data': data})
                case['stimulus'] = dict(initial_ram_q=seed_name, test=test,
                                        held_data=f'{data:02X}')
                cases.append(case)
    paths = [Path(__file__), HERE / 'board_vector_screen.py',
             HERE / 'board_enable_takeover.py', BOARD / 'photo_hypotheses.py',
             BOARD / 'engine.py', BOARD / 'logic.py',
             ASSUMED / 'sequencer.json',
             HERE / 'STATE-FRAME-CROSSCHECK.md']
    report = dict(status='diagnostic held-input screen, not recovered Nokia wiring',
                  fixture=dict(vector_fetch_pc=f'{VECTOR:03X}',
                               target=f'{TARGET:03X}', wait_pc='084',
                               wait_cycle_by_seed=wait_cycles,
                               profile='original q3',
                               initial_ram_q_seeds={'unknown': None, 'zero': 0,
                                                    'ones': 15},
                               controller_frame_examples=['80 02 81 7A',
                                                          'C0 42 81 22',
                                                          'C0 42 81 EA'],
                               held_data_values=[f'{x:02X}' for x in INPUT_BYTES],
                               test_values=[0, 1],
                               data_stimulus='each byte held from external address setup through path termination',
                               prefix='TEST=0 and D=0 until first 084'),
                  outcome_counts=dict(Counter(x['outcome'] for x in cases)),
                  cases=cases,
                  limitations=[
                      'Frame bytes are genuine controller outputs, but no parallel D route or byte timing from controller to DSC2847 is established.',
                      'The one-cycle external ten-bit address driver is hypothetical.',
                      'A held byte is diagnostic; the actual serial frame is four bytes and may reach a different interface.',
                      'The q3 field mapping, D route, TEST source, initial RAM/Q and ADC/DAC route are unresolved.',
                      'This probes only vector 111, ten data bytes, two TEST levels and three RAM/Q startup assumptions, not all timing or command states.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  prom_sha256={chip: cell['rom']['sha256'] for chip, cell in
                               board['components'].items() if cell['type'] == 'PROM'})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['outcome_counts'])
    for case in report['cases']:
        print(case['stimulus'], case['outcome'], case['cycles_after_vector'],
              case['table_calls'], case['call_y'], case['output_site_visits'],
              case['pc_trace_sha256'][:12])
