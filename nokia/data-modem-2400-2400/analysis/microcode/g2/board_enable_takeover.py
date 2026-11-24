"""Test a staged external PROM-address takeover in the full board event model."""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / 'board'
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(BOARD), str(ASSUMED)]
from engine import Engine, validate
from photo_hypotheses import candidate, scenario
from common import save

VECTOR_FETCH = 0x036
CYCLES = 128


def candidate_board():
    board = candidate('q3', 'registered', 'literal')
    board['name'] += '; diagnostic external ten-bit address driver'
    board['external'].update(takeover={'width': 1}, drive={'width': 1},
                             address={'width': 10})
    cells = board['components']
    cells['H_NOT_DRIVE'] = dict(type='NOT', inputs={'A': 'EXT.drive'},
                                connection_status='diagnostic-hypothesis')
    for suffix, start in (('LO', 0), ('HI', 8)):
        bits = [f'EXT.address[{index}]' for index in range(start, min(start + 8, 10))]
        bits += [0] * (8 - len(bits))
        cells[f'H_ADDR_{suffix}'] = dict(
            type='BUFFER', inputs={'D': bits, 'ENn': 'H_NOT_DRIVE.Y'},
            connection_status='diagnostic-hypothesis-no-package-assignment')
    for chip in ('U10', 'U11', 'U17', 'U18'):
        cells[chip]['inputs']['A'] = [
            {'bus': [f'U9.A[{index}]',
                     f'H_ADDR_LO.Y[{index}]' if index < 8 else
                     f'H_ADDR_HI.Y[{index - 8}]']}
            for index in range(10)]
    cells['U9']['inputs']['ENn'] = 'EXT.takeover'
    board['hypotheses']['external_address_takeover'] = (
        'Hypothetical ten-bit driver on all four PROM address buses, with '
        'independent staged controls: disable U9 address outputs, then enable '
        'external driver; reverse the sequence to release. No Nokia net identified.')
    board['limitations'].append(
        'The two eight-bit buffer primitives are a ten-bit diagnostic adapter, '
        'not a claim that the photographed U4 alone drives this bus.')
    errors = validate(board)['errors']
    if errors:
        raise ValueError(errors)
    return board


def run_case(board, takeover):
    fixture = scenario(0)
    fixture['initial_inputs'].update(takeover=0, drive=0, address=VECTOR_FETCH)
    engine = Engine(board, BOARD)
    engine.initialize(fixture['initial_inputs'])
    pcs = []
    first_084 = None
    event = None
    for cycle in range(CYCLES):
        pc = engine.state['U9']['pc'].integer()
        pcs.append(pc)
        if pc == 0x084 and first_084 is None:
            first_084 = cycle
            if takeover:
                initial_stack = (engine.state['U9']['sp'],
                                 engine.state['U9']['stack'][:])
                engine.step({'takeover': 1})
                floating_address = engine.inputs('U10')['A'].text()
                engine.step({'drive': 1})
                driven_address = engine.inputs('U10')['A'].integer()
                prom_bytes = [engine.values[f'U{chip}.D'].integer()
                              for chip in ('10', '11', '17', '18')]
                if floating_address != 'Z' * 10 or driven_address != VECTOR_FETCH:
                    raise ValueError('staged address handoff failed')
                event = dict(cycle=cycle, internal_pc_before=f'{pc:03X}',
                             floating_bus=floating_address,
                             driven_fetch_pc=f'{driven_address:03X}',
                             raw_prom_bytes=prom_bytes)
        for phase in fixture['cycle']:
            engine.step(phase['set'])
            if event is not None and cycle == event['cycle'] and phase['name'] == 'fetch rise':
                event['latched_controls'] = {name: engine.state[name]['q'].integer()
                                             for name in ('U5', 'U6', 'U29', 'U30')}
        if event is not None and cycle == event['cycle']:
            event['internal_pc_after'] = f'{engine.state["U9"]["pc"].integer():03X}'
            event['stack_unchanged'] = (
                engine.state['U9']['sp'] == initial_stack[0] and
                engine.state['U9']['stack'] == initial_stack[1])
            engine.step({'drive': 0})
            engine.step({'takeover': 0})
            event['ordinary_address_after_release'] = f'{engine.inputs("U10")["A"].integer():03X}'
    return dict(cycles=CYCLES, first_084_cycle=first_084,
                final_internal_pc=f'{engine.state["U9"]["pc"].integer():03X}',
                unique_internal_pcs=len(set(pcs)),
                visits_300_3ff=sum(0x300 <= pc <= 0x3ff for pc in pcs),
                table_calls={f'{pc:03X}': pcs.count(pc) for pc in (0x3C2, 0x3D7)},
                most_common_pcs=[(f'{pc:03X}', n) for pc, n in Counter(pcs).most_common(5)],
                event=event)


def run(out=HERE / 'results/board-enable-takeover.json'):
    board = candidate_board()
    baseline = run_case(board, False)
    takeover = run_case(board, True)
    event = takeover['event']
    if (baseline['first_084_cycle'] != 42 or
            baseline['final_internal_pc'] != '084' or
            event['cycle'] != 42 or event['raw_prom_bytes'] != [1, 220, 131, 252] or
            event['internal_pc_after'] != '300' or
            event['ordinary_address_after_release'] != '300' or
            not event['stack_unchanged']):
        raise ValueError('real-PROM board takeover witness changed')
    paths = [Path(__file__), BOARD / 'photo_hypotheses.py',
             BOARD / 'engine.py', BOARD / 'logic.py',
             ASSUMED / 'sequencer.json', ASSUMED / 'common.py']
    report = dict(status='board-model diagnostic, not recovered Nokia wiring',
                  fixture=dict(profile='q3', sequence_source='registered',
                               branch_source='literal', external_test=0,
                               external_data=0, cycles=CYCLES,
                               vector_fetch_pc=f'{VECTOR_FETCH:03X}',
                               address_handoff='U9 EN high, then external drive high; '
                                               'reverse after one complete fetch/execute cycle'),
                  board_address_hypothesis=board['hypotheses']['external_address_takeover'],
                  baseline=baseline, takeover=takeover,
                  limitations=[
                      'No physical U9 EN or ten-bit address-driver path has been traced.',
                      'The base board uses the original q3 field mapping, not the later photo-constrained Am2901 pin assignments.',
                      'The staged controls avoid modeled bus contention; physical gate delays are not simulated.',
                      'A diagnostic word 036 is fetched, not a recovered controller command or vector.',
                      'The board model retains unknown RAM/Q and incomplete arithmetic flag logic.',
                      'No DAC/ADC or controller stream participates, so this is not a modem-function result.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  prom_sha256={chip: cell['rom']['sha256'] for chip, cell in
                               board['components'].items() if cell['type'] == 'PROM'})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['baseline']['first_084_cycle'], report['baseline']['final_internal_pc'])
    print(report['takeover']['event'])
    print(report['takeover']['final_internal_pc'])
