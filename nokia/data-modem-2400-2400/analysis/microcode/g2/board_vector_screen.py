"""Screen every direct real-PROM BRT word as one external address-bus vector."""

import hashlib
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / 'board'
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(BOARD), str(ASSUMED), str(HERE)]
from engine import Engine, Stop
from photo_hypotheses import scenario
from common import decode, read, save, unconditional_transfer
from board_enable_takeover import candidate_board

SEQUENCER = ASSUMED / 'sequencer.json'
BASE_SCENARIO = ASSUMED / 'results/rotation-study/scenario-3.json'
MAX_AFTER_VECTOR = 512
OUTPUT_PCS = set(range(0x392, 0x3A0))


def at_wait(board, fixture):
    engine = Engine(board, BOARD)
    engine.initialize(fixture['initial_inputs'])
    for cycle in range(128):
        if engine.state['U9']['pc'].integer() == 0x084:
            return cycle, engine
        for phase in fixture['cycle']:
            engine.step(phase['set'])
    raise ValueError('baseline did not reach 084 within 128 cycles')


def screen_one(wait_engine, fixture, vector, expected_target):
    engine = deepcopy(wait_engine)
    event = dict(fetch_pc=f'{vector:03X}', target=f'{expected_target:03X}')
    pcs = []
    output_y = []
    try:
        engine.step({'address': vector})
        engine.step({'takeover': 1})
        event['floating_bus'] = engine.inputs('U10')['A'].text()
        engine.step({'drive': 1})
        event['driven_address'] = engine.inputs('U10')['A'].integer()
        event['prom_bytes'] = [engine.values[f'U{chip}.D'].integer()
                               for chip in ('10', '11', '17', '18')]
        before_stack = (engine.state['U9']['sp'], engine.state['U9']['stack'][:])
        for phase in fixture['cycle']:
            engine.step(phase['set'])
        event['internal_pc_after'] = engine.state['U9']['pc'].integer()
        event['stack_unchanged'] = (
            engine.state['U9']['sp'] == before_stack[0] and
            engine.state['U9']['stack'] == before_stack[1])
        engine.step({'drive': 0})
        engine.step({'takeover': 0})
        event['released_address'] = engine.inputs('U10')['A'].integer()
        if (event['floating_bus'] != 'Z'*10 or event['driven_address'] != vector or
                event['internal_pc_after'] != expected_target or
                event['released_address'] != expected_target or
                not event['stack_unchanged']):
            raise ValueError(f'vector {vector:03X}: handoff or BRT contract changed')
        for cycle in range(MAX_AFTER_VECTOR):
            pc = engine.state['U9']['pc'].integer()
            if pc == 0x084:
                outcome = 'returned-to-084'
                break
            pcs.append(pc)
            for phase in fixture['cycle']:
                engine.step(phase['set'])
                if phase['name'] == 'fetch rise' and pc in OUTPUT_PCS:
                    output_y.append(dict(pc=f'{pc:03X}',
                                         y=engine.values['U8.Y'].text() +
                                           engine.values['U2.Y'].text()))
        else:
            outcome = f'{MAX_AFTER_VECTOR}-cycle-bound'
        return dict(**event, outcome=outcome, cycles_after_vector=len(pcs),
                    final_pc=f'{engine.state["U9"]["pc"].integer():03X}',
                    visited_pcs=sorted({f'{pc:03X}' for pc in pcs}),
                    table_calls={f'{pc:03X}': pcs.count(pc) for pc in (0x3C2, 0x3D7)},
                    output_site_visits=len(output_y),
                    known_output_y=sorted({x['y'] for x in output_y
                                           if set(x['y']) <= {'0', '1'}}),
                    output_witness=output_y[:8]), None
    except Stop as error:
        return dict(**event, outcome='model-stop', stop=str(error),
                    cycles_after_vector=len(pcs),
                    final_pc=f'{engine.state["U9"]["pc"].integer():03X}',
                    visited_pcs=sorted({f'{pc:03X}' for pc in pcs}),
                    table_calls={f'{pc:03X}': pcs.count(pc) for pc in (0x3C2, 0x3D7)},
                    output_site_visits=len(output_y),
                    known_output_y=sorted({x['y'] for x in output_y
                                           if set(x['y']) <= {'0', '1'}}),
                    output_witness=output_y[:8]), error


def run(out=HERE / 'results/board-vector-screen.json'):
    board = candidate_board()
    fixture = scenario(0)
    fixture['initial_inputs'].update(takeover=0, drive=0, address=0)
    wait_cycle, wait_engine = at_wait(board, fixture)
    rows = decode(read(SEQUENCER))
    policy = read(BASE_SCENARIO)
    candidates = [(row['pc'], row['branch']) for row in rows
                  if row['command'] == 6 and row['direct'] and
                  unconditional_transfer(row, policy) and row['branch'] != 0x084]
    if len(candidates) != 76:
        raise ValueError('direct BRT vector set changed')
    cases = []
    for vector, target in candidates:
        row, error = screen_one(wait_engine, fixture, vector, target)
        cases.append(row)
    counts = Counter(row['outcome'] for row in cases)
    paths = [Path(__file__), HERE / 'board_enable_takeover.py',
             HERE / 'enable_takeover_probe.py', BOARD / 'photo_hypotheses.py',
             BOARD / 'engine.py', BOARD / 'logic.py', SEQUENCER, BASE_SCENARIO]
    report = dict(status='bounded one-cycle vector screen under hypothetical external address bus',
                  fixture=dict(wait_pc='084', wait_cycle=wait_cycle,
                               profile='original q3', external_test=0,
                               external_data=0, max_cycles_after_vector=MAX_AFTER_VECTOR,
                               candidate_count=len(candidates),
                               handoff='disable U9, enable external address, fetch/execute, disable external address, enable U9'),
                  outcome_counts=dict(counts), cases=cases,
                  limitations=[
                      'No Nokia U9 EN or ten-bit external address connection is established.',
                      'Each vector is a diagnostic choice of one real PROM word, not an observed controller command.',
                      'The base board has the original q3 datapath mapping and unknown power-on RAM/Q.',
                      'TEST and external data are fixed zero; alternate inputs, controller timing and ADC/DAC routes are untested.',
                      'A bounded run or model stop characterizes only that candidate fixture, not the full program.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  prom_sha256={chip: cell['rom']['sha256'] for chip, cell in
                               board['components'].items() if cell['type'] == 'PROM'})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['outcome_counts'])
    print('with table calls', [(x['fetch_pc'], x.get('table_calls'))
                               for x in report['cases'] if sum(x.get('table_calls', {}).values())])
    print('with known output Y', [(x['fetch_pc'], len(x.get('known_output_y', [])))
                                  for x in report['cases'] if x.get('known_output_y')])
