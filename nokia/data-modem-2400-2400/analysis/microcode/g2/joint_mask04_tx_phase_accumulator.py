"""Verify the joint mask04 R1/Y7 phase accumulator on real controller dibits."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_four_row_retention_tx import (
    MAPPINGS, candidate, fixture, hold_candidate, mapped,
    mapping_with_upper_source, split_scenario,
)
from photo_joint_tone_training_data import segment2_from_txd
from photo_main_dibit_pulse import (BASE, PULSE_VISITS, VISITS_PER_SAMPLE,
                                    VISITS_PER_SYMBOL, dibit_rule, scenario_inputs)

TXREADY = HERE / 'results/main-loop-usart-txready.json'
SYMBOLS = 18
LOOP_WORDS = (0x127, 0x128, 0x129, 0x12A)


def run_case(mapping, base, selector, dibits):
    inputs = scenario_inputs(dibits)
    offered_visits = SYMBOLS * VISITS_PER_SYMBOL
    cycles = (offered_visits + 64) * 4
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; verify joint mask04 R1/Y7 transmitter phase recurrence'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    r1 = scenario['initial']['ram'][1]
    previous_phase = None
    first_phase_before_input = None
    visits = 0
    y7_checks = 0
    samples = []
    symbol_ends = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            for address, value in row['registers'].items():
                if address == '1':
                    r1 = value
            pc = row['pc']
            if pc not in LOOP_WORDS:
                continue
            if (row['alu']['y'] ^ r1) & 0x80:
                raise ValueError(('Y7 not R1 high bit', selector, row['cycle'], pc))
            y7_checks += 1
            if pc != 0x127:
                continue
            event = row['external_read']
            if (event['visit'] != visits or
                    event['value'] != inputs[min(visits, len(inputs) - 1)]):
                raise ValueError(('controller input changed', selector, visits))
            if previous_phase is None:
                first_phase_before_input = (r1 - event['value']) & 255
            elif r1 != (previous_phase + event['value']) & 255:
                raise ValueError(('R1 phase recurrence failed', selector, visits))
            previous_phase = r1
            if visits < offered_visits:
                if visits % VISITS_PER_SAMPLE == 0:
                    samples.append(dict(visit=visits, symbol=visits // VISITS_PER_SYMBOL,
                                        sample=visits % VISITS_PER_SYMBOL // VISITS_PER_SAMPLE,
                                        phase=r1, y7=(row['alu']['y'] >> 7) & 1))
                if (visits + 1) % VISITS_PER_SYMBOL == 0:
                    count = visits + 1
                    baseline = (first_phase_before_input + count * BASE) & 255
                    offset = (r1 - baseline) & 255
                    expected = sum(PULSE_VISITS *
                                   (dibit_rule(d & 1, d >> 1) - BASE)
                                   for d in dibits[:count // VISITS_PER_SYMBOL]) & 255
                    if offset != expected:
                        raise ValueError(('dibit phase offset changed', selector,
                                          count, offset, expected))
                    symbol_ends.append(dict(symbol=count // VISITS_PER_SYMBOL - 1,
                                            dibit=dibits[count // VISITS_PER_SYMBOL - 1],
                                            r1=r1, cumulative_offset=offset))
            visits += 1
    if (not result['clean'] or result['completed_cycles'] != cycles or
            visits < offered_visits or len(samples) != SYMBOLS * 8 or
            len(symbol_ends) != SYMBOLS or
            y7_checks != 4 * visits):
        raise ValueError(('joint transmitter loop stopped', selector, visits))
    return dict(selector=selector, dibits=dibits, cycles=cycles,
                pc127_visits=visits, r1_recurrence_checks=visits - 1,
                y7_equals_r1_high_checks=y7_checks,
                initial_phase_before_first_input=first_phase_before_input,
                symbol_ends=symbol_ends, first_16_samples=samples[:16],
                sampled_y7_sha256=hashlib.sha256(bytes(row['y7'] for row in samples)).hexdigest(),
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/joint-mask04-tx-phase-accumulator.json'):
    txready = json.loads(TXREADY.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        tx_case = next(row for row in txready['cases']
                       if row['selector'] == selector)
        dibits = segment2_from_txd(tx_case)[:SYMBOLS]
        case = run_case(mapping, base, selector, dibits)
        cases.append(case)
        print(selector, 'dibits', dibits, 'visits', case['pc127_visits'],
              'Y7 checks', case['y7_equals_r1_high_checks'], flush=True)
    paths = (Path(__file__), TXREADY,
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'split_slice_probe.py',
             HERE / 'photo_controller_path.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='joint mask04 executed R1/Y7 phase accumulator on controller data',
                  fixture=dict(controller_selectors=['40', '60'],
                               symbols_per_selector=SYMBOLS,
                               visits_per_symbol=VISITS_PER_SYMBOL,
                               visits_per_sample=VISITS_PER_SAMPLE,
                               dibit_pulse_visits=PULSE_VISITS,
                               baseline_d127=BASE,
                               mapping='joint upper-source lower mask04'),
                  cases=cases,
                  limitations=['D127 input, four-visit dibit pulse, slice links, clock and Y7-to-DAC path are board hypotheses.',
                               'The experiment verifies arithmetic on the first 18 controller-derived A4 dibits; full-stream output remains in the linked transmitter replays.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
