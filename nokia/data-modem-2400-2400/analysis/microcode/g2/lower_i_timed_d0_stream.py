"""Replay 8031 bits through one candidate D3F8 pin at clock-derived holds."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from controller_bit_dispatch import (ANALYSIS, CORE, CONTROLLER_ROM,
                                     controller_stream)
from execute import execute
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

INPUT_PC = 0x3F8
ROM_PC = 0x3F7
OUTPUT_PCS = (0x3F8, 0x3F9, 0x3FA)
FIXED_HOLDS = (188, 250, 375, 750)
ENCODINGS = ((8, 9), (9, 8))


def values_for(bits, zero, one, lengths):
    if len(bits) != len(lengths):
        raise ValueError('bit/hold schedule length mismatch')
    return [value for bit, length in zip(bits, lengths)
            for value in [zero if bit == 0 else one] * length]


def scenario_for(base, values, label):
    scenario = copy.deepcopy(base)
    scenario['name'] += f'; timed D3F8 D0 candidate {label}'
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = values
    return scenario


def run_case(mapping, base, values, label, trace=False):
    cycles = 8 * len(values) + 80
    scenario = scenario_for(base, values, label)
    if trace:
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            rows = [json.loads(line) for line in
                    (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        if not result['clean'] or len(rows) != cycles:
            raise ValueError('timed D0 trace did not complete')
        return result, rows
    result = execute(mapping, scenario, cycles, mode='integrated', trace_limit=0)
    if not result['clean']:
        raise ValueError('timed D0 run did not complete')
    return result, None


def site_values(trace, pc, field):
    rows = [row for row in trace if row['pc'] == pc]
    if field == 'rom_address':
        return [row['external_read']['address'] for row in rows
                if row['external_read'].get('selected_by_alu')]
    return [row['alu']['y'] for row in rows]


def first_difference(left, right):
    return next((index for index, (a, b) in enumerate(zip(left, right))
                 if a != b), None)


def run(out=HERE / 'results/lower-i-timed-d0-stream.json'):
    _, bits = controller_stream()
    if len(bits) != 128 or bits[:4] != [0, 0, 0, 1]:
        raise ValueError('controller bit source changed')
    _, unmodified = fixture()
    base = split_scenario(unmodified)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')
    schedules = []
    for zero, one in ENCODINGS:
        for hold in FIXED_HOLDS:
            values = values_for(bits, zero, one, [hold] * len(bits))
            result, _ = run_case(mapping, base, values,
                                 f'{zero:X}/{one:X} hold {hold}')
            visits = result['read_sequence_visits'].get(INPUT_PC, 0)
            schedules.append(dict(zero=zero, one=one, schedule=f'fixed_{hold}',
                                  offered_visits=len(values), consumed_visits=visits,
                                  consumed_all_bits=visits >= len(values),
                                  selected_rom_visits=result['address_counts'].get(ROM_PC, 0),
                                  final_pc=result['final_state']['pc'],
                                  trace_digest=result['trace_digest']))
        for start in (187, 188):
            lengths = [start if index % 2 == 0 else 375 - start
                       for index in range(len(bits))]
            values = values_for(bits, zero, one, lengths)
            result, _ = run_case(mapping, base, values,
                                 f'{zero:X}/{one:X} alternating {start}/{375-start}')
            visits = result['read_sequence_visits'].get(INPUT_PC, 0)
            schedules.append(dict(zero=zero, one=one,
                                  schedule=f'alternating_{start}_{375-start}',
                                  offered_visits=len(values), consumed_visits=visits,
                                  consumed_all_bits=visits >= len(values),
                                  selected_rom_visits=result['address_counts'].get(ROM_PC, 0),
                                  final_pc=result['final_state']['pc'],
                                  trace_digest=result['trace_digest']))
    witnesses = []
    prefix = bits[:4]
    for zero, one in ENCODINGS:
        offered = values_for(prefix, zero, one, [750] * len(prefix))
        result, trace = run_case(mapping, base, offered,
                                 f'{zero:X}/{one:X}, first four bits', True)
        zero_result, zero_trace = run_case(mapping, base, [zero] * len(offered),
                                           f'{zero:X} control', True)
        inputs = [row for row in trace if row['pc'] == INPUT_PC]
        if (len(inputs) < len(offered) or
                [row['external_read']['value'] for row in inputs[:len(offered)]] != offered or
                any(not row['external_read']['selected_by_alu']
                    for row in inputs[:len(offered)])):
            raise ValueError('candidate timed D0 bits not selected at D3F8')
        gaps = {b['cycle'] - a['cycle'] for a, b in
                zip(inputs[8:len(offered)-1], inputs[9:len(offered)])}
        sites = {}
        for pc, field in ((ROM_PC, 'rom_address'),
                          *[(pc, 'alu_y') for pc in OUTPUT_PCS]):
            actual = site_values(trace, pc, field)[:len(offered)]
            control = site_values(zero_trace, pc, field)[:len(offered)]
            if len(actual) != len(offered) or len(control) != len(offered):
                raise ValueError('timed D0 ROM/ALU site visits missing')
            sites[f'{pc:03X}_{field}'] = dict(
                distinct_controller_values=len(set(actual)),
                first_difference_from_zero=first_difference(actual, control),
                changed_after_first_bit=sum(a != b for a, b in
                                            zip(actual[2250:], control[2250:])),
                first_16_after_transition=actual[2250:2266])
        witnesses.append(dict(zero=zero, one=one, input_cycle_gaps=sorted(gaps),
                              selected_input_visits=len(offered), sites=sites,
                              trace_digests=dict(controller=result['trace_digest'],
                                                 zero=zero_result['trace_digest'])))
    full = {(row['zero'], row['one'], row['schedule']) for row in schedules
            if row['consumed_all_bits']}
    expected_full = {(zero, one, f'fixed_{hold}')
                     for zero, one in ENCODINGS for hold in (188, 750)}
    if full != expected_full:
        raise ValueError('timed D0 full-stream classification changed')
    if any(witness['input_cycle_gaps'] != [8] or
           any(site['first_difference_from_zero'] is None or
               site['changed_after_first_bit'] == 0
               for site in witness['sites'].values())
           for witness in witnesses):
        raise ValueError('timed D0 ROM/ALU transition witness changed')
    paths = [Path(__file__), HERE / 'lower_i_prom_data_route.py',
             HERE / 'controller_bit_dispatch.py',
             ANALYSIS / 'controller_scrambler.py',
             ANALYSIS / 'interface_probe.c',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c')),
             CONTROLLER_ROM, HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', ASSUMED / 'execute.py',
             HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='timed single-D0 controller-to-ROM path under candidate mapping',
                  fixture=dict(mapping=mapping['name'], q=5,
                               controller_bits='128 locally ROM-executed 8031 scrambler bits',
                               zero_one_d3f8_bytes=['08/09', '09/08'],
                               candidate_clock='14.4 MHz/k, k=1..4',
                               microcycles_per_loop_visit=8,
                               nominal_data_bits_per_second=2400,
                               fixed_holds=list(FIXED_HOLDS),
                               alternating_k4_holds=['187/188', '188/187']),
                  totals=dict(schedules=len(schedules),
                              full_stream_schedules=sum(row['consumed_all_bits']
                                                        for row in schedules)),
                  schedules=schedules, transition_witnesses=witnesses,
                  limitations=[
                      'D3F8 D0 from controller bit, D3 held high, D2/D1 low, paired PROM-data latch routes and initial Q are hypotheses.',
                      'The 8031 scrambler executes locally; no physical USART-to-DSP phase or sequencer divider has been measured.',
                      'A selected ROM/ALU stream is not a DAC08 sample stream or proof of the transmit waveform.',
                      'The 14.4 MHz undivided clock assumption gives 750 loop visits per 2400 bit/s bit only in this eight-microcycle loop.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
