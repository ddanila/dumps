"""Screen direct real-PROM BSR words as one-cycle external address vectors."""

import hashlib
from collections import Counter
from pathlib import Path

from board_enable_takeover import candidate_board
from board_vector_screen import (ASSUMED, BASE_SCENARIO, BOARD, SEQUENCER,
                                 at_wait, screen_one)
from common import decode, read, save, unconditional_transfer
from photo_hypotheses import scenario

HERE = Path(__file__).resolve().parent


def run(out=HERE / 'results/board-call-vector-screen.json'):
    board = candidate_board()
    fixture = scenario(0)
    fixture['initial_inputs'].update(takeover=0, drive=0, address=0)
    wait_cycle, wait_engine = at_wait(board, fixture)
    rows = decode(read(SEQUENCER))
    policy = read(BASE_SCENARIO)
    candidates = [(row['pc'], row['branch']) for row in rows
                  if row['command'] == 4 and row['direct'] and
                  unconditional_transfer(row, policy)]
    if len(candidates) != 77:
        raise ValueError('direct BSR vector set changed')
    cases = []
    for vector, target in candidates:
        row, _ = screen_one(wait_engine, fixture, vector, target,
                            stack_action='call')
        cases.append(row)
    paths = [Path(__file__), HERE / 'board_vector_screen.py',
             HERE / 'board_enable_takeover.py',
             BOARD / 'photo_hypotheses.py', BOARD / 'engine.py',
             BOARD / 'logic.py', SEQUENCER, BASE_SCENARIO]
    report = dict(status='bounded one-cycle call-vector screen under hypothetical external address bus',
                  fixture=dict(wait_pc='084', wait_cycle=wait_cycle,
                               profile='original q3', external_test=0,
                               external_data=0, initial_ram_q='unknown',
                               max_cycles_after_vector=512,
                               candidate_count=len(candidates),
                               encoded_target_count=len(set(target for _, target in candidates)),
                               return_address='085',
                               handoff='U9 off, external address on, fetch/execute one BSR, external address off, U9 on'),
                  outcome_counts=dict(Counter(x['outcome'] for x in cases)),
                  cases=cases,
                  limitations=[
                      'No Nokia U9 EN or ten-bit external address-driver connection is established.',
                      'A real-PROM BSR word is fetched diagnostically, not as a recovered controller command.',
                      'The return address 085 follows from internal PC 084 during the diagnostic call, not a recovered caller.',
                      'The base board has the original q3 datapath mapping and unknown power-on RAM/Q.',
                      'TEST and external D are held zero; controller stream, other timing, ADC/DAC routes and alternate mappings are untested.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  prom_sha256={chip: cell['rom']['sha256'] for chip, cell in
                               board['components'].items() if cell['type'] == 'PROM'})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['outcome_counts'])
    print('output sites', [(x['fetch_pc'], x['output_site_visits'])
                           for x in report['cases'] if x['output_site_visits']])
    print('table calls', [(x['fetch_pc'], x['table_calls'])
                          for x in report['cases'] if any(x['table_calls'].values())])
