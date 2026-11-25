"""Find two-nibble D3F8 encodings that carry a real 8031 bitstream."""

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
from lower_i_held_nibble_cycles import INPUT_PC, ROM_PC
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

LIVE = (1, 2, 3, 4, 5, 7, 8, 9, 12, 15)
HOLDS = (1, 2, 4, 8, 16)
ALU_PCS = (0x3F8, 0x3F9, 0x3FA)


def scenario_for(base, values, label):
    scenario = copy.deepcopy(base)
    scenario['name'] += f'; D3F8 nibble stream {label}'
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = values
    return scenario


def run_case(mapping, base, values, label, trace=False):
    cycles = 9 * len(values) + 80
    scenario = scenario_for(base, values, label)
    if trace:
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            rows = [json.loads(line) for line in
                    (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        if not result['clean'] or len(rows) != cycles:
            raise ValueError('controller nibble trace incomplete')
        return result, rows
    result = execute(mapping, scenario, cycles, mode='integrated', trace_limit=0)
    if not result['clean']:
        raise ValueError('controller nibble run incomplete')
    return result, None


def encoding(bits, zero, one, hold):
    return [level for bit in bits
            for level in [zero if bit == 0 else one] * hold]


def site_values(trace, pc, key):
    rows = [row for row in trace if row['pc'] == pc]
    if key == 'rom_address':
        return [row['external_read']['address'] for row in rows
                if row['external_read'].get('selected_by_alu')]
    return [row['alu']['y'] for row in rows]


def run(out=HERE / 'results/lower-i-nibble-stream-bridge.json'):
    _, bits = controller_stream()
    if len(bits) != 128 or set(bits) != {0, 1}:
        raise ValueError('controller bit source changed')
    _, unmodified = fixture()
    base = split_scenario(unmodified)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')
    pair_cases = []
    survivors = []
    for zero in LIVE:
        for one in LIVE:
            if zero == one:
                continue
            values = encoding(bits, zero, one, 1)
            result, _ = run_case(mapping, base, values, f'{zero:X}/{one:X}, hold 1')
            visits = result['read_sequence_visits'].get(INPUT_PC, 0)
            pair_cases.append(dict(zero=zero, one=one, d3f8_visits=visits,
                                   consumed_all_bits=visits >= len(values),
                                   rom_visits=result['address_counts'].get(ROM_PC, 0),
                                   final_pc=result['final_state']['pc'],
                                   trace_digest=result['trace_digest']))
            if visits >= len(values):
                survivors.append((zero, one))
    held_cases = []
    for zero, one in survivors:
        for hold in HOLDS[1:]:
            values = encoding(bits, zero, one, hold)
            result, _ = run_case(mapping, base, values,
                                 f'{zero:X}/{one:X}, hold {hold}')
            visits = result['read_sequence_visits'].get(INPUT_PC, 0)
            held_cases.append(dict(zero=zero, one=one, hold=hold,
                                   offered_visits=len(values), consumed_visits=visits,
                                   consumed_all_bits=visits >= len(values),
                                   final_pc=result['final_state']['pc']))
    witnesses = []
    for zero, one in survivors:
        values = encoding(bits, zero, one, 1)
        result, trace = run_case(mapping, base, values, f'{zero:X}/{one:X}', True)
        control_zero, trace_zero = run_case(mapping, base, [zero] * 128,
                                            f'{zero:X} held', True)
        control_one, trace_one = run_case(mapping, base, [one] * 128,
                                          f'{one:X} held', True)
        input_rows = [row for row in trace if row['pc'] == INPUT_PC]
        first = input_rows[:128]
        if ([row['external_read']['value'] for row in first] != values or
                any(not row['external_read']['selected_by_alu'] for row in first)):
            raise ValueError('controller nibble bytes not selected at D3F8')
        differences = {}
        for pc, key in ((ROM_PC, 'rom_address'),
                        *[(pc, 'alu_y') for pc in ALU_PCS]):
            actual = site_values(trace, pc, key)[:128]
            all_zero = site_values(trace_zero, pc, key)[:128]
            all_one = site_values(trace_one, pc, key)[:128]
            if len(actual) != 128 or len(all_zero) != 128 or len(all_one) != 128:
                raise ValueError('controller/control site visits missing')
            differences[f'{pc:03X}_{key}'] = dict(
                distinct_controller_values=len(set(actual)),
                differs_from_zero=sum(a != b for a, b in zip(actual, all_zero)),
                differs_from_one=sum(a != b for a, b in zip(actual, all_one)),
                first_16_controller=actual[:16])
        gaps = [right['cycle'] - left['cycle']
                for left, right in zip(input_rows[8:127], input_rows[9:128])]
        witnesses.append(dict(zero=zero, one=one,
                              input_cycle_gaps=sorted(set(gaps)),
                              selected_input_bytes=128,
                              site_differences=differences,
                              trace_digests=dict(controller=result['trace_digest'],
                                                 zero=control_zero['trace_digest'],
                                                 one=control_one['trace_digest'])))
    paths = [Path(__file__), HERE / 'lower_i_held_nibble_cycles.py',
             HERE / 'lower_i_prom_data_route.py',
             HERE / 'controller_bit_dispatch.py',
             ANALYSIS / 'controller_scrambler.py',
             ANALYSIS / 'interface_probe.c',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c')),
             CONTROLLER_ROM,
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             ASSUMED / 'execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='conditional 8031-bit to repeated ROM/ALU path via D3F8 nibble encoding',
                  fixture=dict(mapping=mapping['name'], q=5,
                               bits='128 ROM-executed 8031 scrambler bits',
                               input_pc='3F8', rom_pc='3F7',
                               held_input_levels=[f'{v:X}' for v in LIVE],
                               holds=list(HOLDS),
                               cycle_limit='9*offered D3F8 visits + 80'),
                  totals=dict(pairs=len(pair_cases), full_stream_pairs=len(survivors),
                              full_stream_pairs_at_longer_holds=sum(
                                  row['consumed_all_bits'] for row in held_cases)),
                  pair_cases=pair_cases, held_cases=held_cases, witnesses=witnesses,
                  limitations=[
                      'The controller bit-to-D3F8 nibble encoder, input timing and all PROM/latch pin routes are untraced.',
                      'The 8031 scrambler bytes are executed locally; this is not a complete controller-DSP co-simulation.',
                      'One new bit per eight-microcycle loop visit is much faster than the 2400 bit/s data stream under the 14.4 MHz/k, k=1..4, clock hypothesis.',
                      'ROM addresses and ALU Y are internal; no DAC08 sample, line carrier or receive bit is established.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
