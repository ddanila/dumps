"""Verify the mask-04 ADC lookup and Q-to-R1 wrapper transfer in real traces."""

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
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import CYCLES, PATTERNS, configured

MASKS = (4, 8)


def capture(mapping, base, mask, pattern, rom):
    samples = codes(pattern, 32, 'complementary')
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != 1500:
        raise ValueError('four-row held ADC schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    q = scenario['initial']['q']
    pc_digest = hashlib.sha256()
    wrapper_q = []
    wrapper_r1 = []
    consumer_y = []
    after_fourth = []
    wrapper_instructions = Counter()
    adc_instructions = Counter()
    checks = Counter()
    pending_y = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3F8, 0) != 1500 or
                result['address_counts'].get(0x3FE, 0) != 1500 or
                result['read_sequence_visits'].get(0x3F8, 0) != 1500):
            raise ValueError(('joint receive rule execution changed', mask,
                              pattern))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            old_q = q
            if pc == 0x3EB:
                pair = (row['instruction_i'], row['instruction_i_high'])
                wrapper_instructions[pair] += 1
                if mask == 4 and (pair != (0x92, 0x97) or
                                  row['carry_in'] != 1 or
                                  row['external_read']['value'] != 1):
                    raise ValueError('mask-04 wrapper operand/field changed')
                if mask == 8 and pair != (0x94, 0xC7):
                    raise ValueError('mask-08 wrapper instruction changed')
            elif pc == 0x3F8:
                pair = (row['instruction_i'], row['instruction_i_high'])
                adc_instructions[pair] += 1
                if mask == 4:
                    if pair != (0xD4, 0xC5) or row['register_address_a'] != 5 or row['register_address_b'] != 11:
                        raise ValueError('mask-04 ADC instruction/address changed')
                    code = row['external_read']['value']
                    low_total = ((~ram[5]) & 15) + row['carry_in']
                    high_total = (code >> 4) + (ram[5] >> 4) + (low_total >> 4)
                    expected_y = (low_total & 15) | ((high_total & 15) << 4)
                    if (not row['external_read'].get('selected_by_alu') or
                            code != values[checks['adc_equations']] or
                            row['alu']['y'] != expected_y or
                            row['alu']['f'] != expected_y):
                        raise ValueError(('mask-04 ADC equation changed',
                                          checks['adc_equations']))
                    checks['adc_equations'] += 1
                pending_y = row['alu']['y']
            elif pc == 0x3F9:
                event = row['external_read']
                if (pending_y is None or not event.get('selected_by_alu') or
                        event['address'] != 256 + pending_y or
                        event['value'] != rom[event['address']]):
                    raise ValueError(('ADC-derived ROM lookup changed', mask))
                checks['adc_rom_lookups'] += 1
                pending_y = None
            elif pc == 0x3ED and mask == 4:
                if ((row['instruction_i'], row['instruction_i_high']) !=
                        (0xA0, 0xA1) or
                        row['register_address_a'] != 1 or
                        row.get('register_address_a_high',
                                row['register_address_a']) != 1 or
                        row['alu']['y'] != ram[1]):
                    raise ValueError('mask-04 3ED R1-to-Y consumer changed')
                consumer_y.append(row['alu']['y'])
                checks['r1_y_consumptions'] += 1
            for address, value in row['registers'].items():
                ram[int(address)] = value
            q = row['q']
            if pc == 0x3EB:
                if mask == 4 and ram[1] != (- (old_q & 15)) & 255:
                    raise ValueError('mask-04 Q-low to R1 rule changed')
                if mask == 8 and ram[1] != 0x10:
                    raise ValueError('mask-08 R1 fixed-point changed')
                wrapper_q.append(old_q)
                wrapper_r1.append(ram[1])
                checks['wrapper_rules'] += 1
            elif pc == 0x3FE:
                after_fourth.append(bytes(ram) + bytes((q,)))
    if (checks['wrapper_rules'] != 6001 or
            checks['adc_rom_lookups'] != 1500 or
            (mask == 4 and checks['adc_equations'] != 1500) or
            (mask == 4 and checks['r1_y_consumptions'] != 6000) or
            len(after_fourth) != 1500):
        raise ValueError(('rule count changed', mask, checks))
    return dict(mask=mask, pattern=list(pattern), checks=dict(checks),
                wrapper_instructions={f'{lo:02X}/{hi:02X}': count
                                      for (lo, hi), count in wrapper_instructions.items()},
                adc_instructions={f'{lo:02X}/{hi:02X}': count
                                  for (lo, hi), count in adc_instructions.items()},
                distinct_wrapper_r1=len(set(wrapper_r1)),
                pc_digest=pc_digest.hexdigest(),
                trace_digest=result['trace_digest'],
                wrapper_q=wrapper_q, wrapper_r1=wrapper_r1,
                consumer_y=consumer_y,
                after_fourth=after_fourth)


def run(out=HERE / 'results/joint-mask04-adc-rom-wrapper-rule.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    _, base = fixture()
    rom = ROM.read_bytes()
    cases = []
    for mask in MASKS:
        mapping = candidate(receiver, transmitter, mask)
        for pattern in PATTERNS:
            cases.append(capture(mapping, base, mask, pattern, rom))
            print('checked', mask, pattern, flush=True)
    comparisons = []
    for mask in MASKS:
        full, zero = (row for row in cases if row['mask'] == mask)
        if full['pc_digest'] != zero['pc_digest']:
            raise ValueError(('paired PC path changed', mask))
        comparisons.append(dict(mask=mask,
                                wrapper_q_differences=sum(a != b for a, b in
                                                          zip(full['wrapper_q'], zero['wrapper_q'])),
                                wrapper_r1_differences=sum(a != b for a, b in
                                                           zip(full['wrapper_r1'], zero['wrapper_r1'])),
                                consumer_y_differences=sum(a != b for a, b in
                                                           zip(full['consumer_y'], zero['consumer_y']))
                                if mask == 4 else None,
                                after_fourth_state_differences=sum(a != b for a, b in
                                                                 zip(full['after_fourth'], zero['after_fourth']))))
    if ([row['after_fourth_state_differences'] for row in comparisons] != [1312, 0] or
            [row['wrapper_r1_differences'] for row in comparisons][1] != 0):
        raise ValueError('joint map retention comparison changed')
    report_cases = [{key: value for key, value in row.items()
                     if key not in ('wrapper_q', 'wrapper_r1', 'consumer_y',
                                    'after_fourth')}
                    for row in cases]
    paths = [Path(__file__), HERE / 'joint_four_row_retention_tx.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'], ROM,
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='mask-04 ADC-to-ROM equation and Q-to-R1 wrapper transfer',
        fixture=dict(masks=MASKS, patterns=PATTERNS,
                     mapping='joint upper-source candidate with lower masks 04 and 08',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample'),
        cases=report_cases, comparisons=comparisons,
        limitations=[
            'The input/field wiring, TEST source and dispatch remain photo-compatible hypotheses.',
            'An ADC-dependent table lookup and retained R1 are not a received dibit or echo cancellation.',
            'The 3EB D=1 level is a scenario input, not a traced source.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['comparisons'])
