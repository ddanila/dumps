"""Locate the first internal effect of a selected PC129 ROM-bank change."""

import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_four_row_retention_tx import (
    MAPPINGS, candidate, fixture, hold_candidate, mapped,
    mapping_with_upper_source, split_scenario,
)

CYCLES = 4096
TONE_BYTE = 0x88
TONE_VISITS = 1200


def scenario(base, bank):
    result = split_scenario(hold_candidate(base))
    result['name'] += '; isolate PC129 selected Am27S31 bank'
    result['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        result['inputs']['register_address_bit_overrides']['a'])
    for policy in result['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    result['initial']['q'] = 0
    result['io']['read']['pc_sequences'][str(0x127)] = [TONE_BYTE] * TONE_VISITS
    result['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    result['io']['read']['address']['bank_by_pc'] = {
        str(0x129): bank, str(0x12E): 256}
    return result


def execute_case(mapping, base, bank):
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario(base, bank), CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        rows = [json.loads(line) for line in
                (Path(temporary) / 'trace.jsonl').open()]
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            len(rows) != CYCLES or result['address_counts'].get(0x129) != 1014 or
            result['read_sequence_visits'].get(0x127) != 1014):
        raise ValueError('tone-window PROM execution changed')
    return result, rows


def run(out=HERE / 'results/joint-mask04-tx-rom-impact.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    upper, upper_rows = execute_case(mapping, base, 256)
    lower, lower_rows = execute_case(mapping, base, 0)
    differences = {key: [] for key in ('pc', 'next_pc', 'rom_byte',
                                       'alu_f', 'alu_y', 'alu_y7', 'q',
                                       'flags', 'registers')}
    by_pc = {key: Counter() for key in differences}
    sampled = {phase: dict(visits=0, y_differences=0)
               for phase in range(4)}
    selected = 0
    first = None
    for index, (left, right) in enumerate(zip(upper_rows, lower_rows)):
        if left['pc'] == 0x129:
            if not (left['external_read']['selected_by_alu'] and
                    right['external_read']['selected_by_alu']):
                raise ValueError('PC129 ROM operand not selected')
            selected += 1
        values = dict(
            pc=(left['pc'], right['pc']),
            next_pc=(left['next_pc'], right['next_pc']),
            rom_byte=(left.get('external_read', {}).get('value'),
                      right.get('external_read', {}).get('value')),
            alu_f=(left['alu']['f'], right['alu']['f']),
            alu_y=(left['alu']['y'], right['alu']['y']),
            alu_y7=(left['alu']['y'] & 0x80, right['alu']['y'] & 0x80),
            q=(left['q'], right['q']),
            flags=({key: left['alu'][key] for key in
                    ('carry', 'overflow', 'sign', 'zero')},
                   {key: right['alu'][key] for key in
                    ('carry', 'overflow', 'sign', 'zero')}),
            registers=(left['registers'], right['registers']))
        for key, (a, b) in values.items():
            if a != b:
                differences[key].append(index)
                by_pc[key][f'{left["pc"]:03X}'] += 1
                if first is None:
                    first = dict(cycle=index, pc=f'{left["pc"]:03X}',
                                 upper=dict(rom=left.get('external_read'),
                                            alu=left['alu'],
                                            registers=left['registers']),
                                 lower=dict(rom=right.get('external_read'),
                                            alu=right['alu'],
                                            registers=right['registers']))
        if index >= 40 and (index - 40) % 1500 < 4:
            phase = (index - 40) % 1500
            sampled[phase]['visits'] += 1
            sampled[phase]['y_differences'] += (
                left['alu']['y'] != right['alu']['y'])
    paths = (Path(__file__), HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'split_slice_probe.py', HERE / 'photo_controller_path.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='first selected-ROM-bank effect in the joint mask04 transmitter',
                  fixture=dict(cycles=CYCLES, pc127_tone_byte=TONE_BYTE,
                               offered_tone_visits=TONE_VISITS,
                               bank_upper=256, bank_lower=0,
                               pc12e_bank=256),
                  selected_pc129_reads=selected,
                  traces=dict(upper=upper['trace_digest'],
                              lower=lower['trace_digest']),
                  final_states=dict(upper=upper['final_state'],
                                    lower=lower['final_state']),
                  first_difference=first,
                  free_clock_sample_window=sampled,
                  differences={key: dict(count=len(indices),
                                         first_cycles=indices[:8],
                                         by_pc=dict(by_pc[key]))
                               for key, indices in differences.items()},
                  limitations=['This is the first 4,096 cycles of an assumed controller-fed tone-mode route.',
                               'It tests a selected ROM-bank intervention, not the physical A8 net or DAC path.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['differences'])
