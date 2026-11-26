"""Verify the selected PC129 ROM byte reaches 12A Y0 through carry."""

import hashlib
import json
import tempfile
from pathlib import Path

from joint_mask04_tx_rom_impact import (CYCLES, HERE, MAPPINGS, candidate,
                                        execute, fixture, mapped,
                                        mapping_with_upper_source, scenario)
from photo_main_dibit_pulse import scenario_inputs

OUT = HERE / 'results/joint-mask04-tx-rom-carry-equation.json'
INPUTS = {'tone_88': [0x88] * 1200,
          'data_11_then_b0': scenario_inputs([3])}


def execute_and_audit(mapping, base, bank, name, values):
    configured = scenario(base, bank)
    configured['io']['read']['pc_sequences'][str(0x127)] = values
    ram = configured['initial']['ram'][:]
    pairs = []
    previous_129 = None
    pc_path = hashlib.sha256()
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, configured, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x129) != 1014 or
                result['address_counts'].get(0x12A) != 1014):
            raise ValueError(('short PROM fixture changed', name, bank))
        for raw in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(raw)
            pc = row['pc']
            pc_path.update(pc.to_bytes(2, 'little'))
            a, b = ram[1], ram[0]
            carry_in = row['carry_in']
            if pc == 0x129:
                if (row['instruction_i'] != 0xC9 or
                        row['instruction_i_high'] != 0x8D or
                        (row['register_address_a'], row['register_address_b']) != (1, 0) or
                        not row['external_read']['selected_by_alu']):
                    raise ValueError(('129 instruction/ROM selection changed', name, bank))
                d = row['external_read']['value']
                low_total = (15 - (a & 15)) + (b & 15) + carry_in
                high_total = (15 - (d >> 4)) + (a >> 4) + (low_total >> 4)
                expected_f = ((high_total & 15) << 4) | (low_total & 15)
                expected_y = (a & 0xF0) | (low_total & 15)
                expected_carry = (high_total >> 4) & 1
                if ((row['alu']['f'], row['alu']['y'], row['alu']['carry']) !=
                        (expected_f, expected_y, expected_carry) or
                        row['registers'] != {'0': expected_f}):
                    raise ValueError(('129 split-slice equation failed', name, bank,
                                      row['cycle']))
                previous_129 = dict(address=row['external_read']['address'],
                                    rom_byte=d, r1=a, r0_before=b,
                                    f=expected_f, carry=expected_carry)
            elif pc == 0x12A:
                if (previous_129 is None or row['instruction_i'] != 0xC1 or
                        row['instruction_i_high'] != 0x85 or
                        (row['register_address_a'], row['register_address_b']) != (1, 0) or
                        row['external_read']['value'] != 1 or
                        carry_in != previous_129['carry'] or
                        b != previous_129['f']):
                    raise ValueError(('129-to-12A carry/R0 chain broke', name, bank,
                                      row['cycle']))
                low_base = (a & 15) + (b & 15)
                low_total = low_base + carry_in
                high_total = (a >> 4) + (low_total >> 4)
                expected_f = ((high_total & 15) << 4) | (low_total & 15)
                expected_y = (a & 0xF0) | (low_total & 15)
                expected_carry = (high_total >> 4) & 1
                if ((row['alu']['f'], row['alu']['y'], row['alu']['carry']) !=
                        (expected_f, expected_y, expected_carry) or
                        row['registers'] != {'0': expected_f}):
                    raise ValueError(('12A split-slice equation failed', name, bank,
                                      row['cycle']))
                pairs.append(dict(**previous_129,
                                  r1_at_12a=a, r0_at_12a=b,
                                  r0_low_at_12a=b & 15,
                                  low_sum_before_carry=low_base,
                                  carry_in_12a=carry_in,
                                  y_12a=expected_y,
                                  f_12a=expected_f))
                previous_129 = None
            for address, value in row['registers'].items():
                ram[int(address)] = value
    if len(pairs) != 1014:
        raise ValueError(('incomplete 129-to-12A pairs', name, bank))
    return result, pc_path.hexdigest(), pairs


def compare(upper, lower):
    if len(upper) != len(lower):
        raise ValueError('bank trace lengths differ')
    keys = ('rom_byte', 'f', 'carry', 'r1', 'r0_before',
            'r1_at_12a', 'r0_at_12a', 'r0_low_at_12a',
            'low_sum_before_carry',
            'carry_in_12a', 'y_12a', 'f_12a')
    differences = {key: sum(a[key] != b[key] for a, b in zip(upper, lower))
                   for key in keys}
    if (differences['rom_byte'] != len(upper) or
            differences['r1'] or differences['r0_before'] or
            differences['r1_at_12a'] or differences['r0_low_at_12a'] or
            differences['low_sum_before_carry'] or
            differences['carry'] != differences['carry_in_12a'] or
            differences['carry'] != differences['y_12a'] or
            any((a['y_12a'] ^ b['y_12a']) not in (0, 1)
                for a, b in zip(upper, lower)) or
            any((a['carry'] != b['carry']) != (a['y_12a'] != b['y_12a'])
                for a, b in zip(upper, lower))):
        raise ValueError(('ROM carry does not explain Y0', differences))
    return dict(pairs=len(upper), differences=differences,
                xor_masks=sorted({a['y_12a'] ^ b['y_12a']
                                  for a, b in zip(upper, lower)}),
                first_y_difference_indices=[index for index, (a, b) in
                                            enumerate(zip(upper, lower))
                                            if a['y_12a'] != b['y_12a']][:16],
                first_pair_upper=upper[0], first_pair_lower=lower[0])


def run(out=OUT):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for name, values in INPUTS.items():
        upper_result, upper_path, upper = execute_and_audit(
            mapping, base, 256, name, values)
        lower_result, lower_path, lower = execute_and_audit(
            mapping, base, 0, name, values)
        if upper_path != lower_path:
            raise ValueError(('ROM bank changed PC path', name))
        contrast = compare(upper, lower)
        cases.append(dict(input=name,
                          d127_prefix=[f'{value:02X}' for value in values[:8]],
                          bank_upper_trace_digest=upper_result['trace_digest'],
                          bank_lower_trace_digest=lower_result['trace_digest'],
                          common_pc_path_sha256=upper_path,
                          **contrast))
        print('ROM carry', name, contrast['differences'], flush=True)
    paths = (Path(__file__), HERE / 'joint_mask04_tx_rom_impact.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='PC129 ROM byte to PC12A Y0 split-slice carry equation',
                  fixture=dict(cycles_per_run=CYCLES,
                               selected_pc129_visits_per_run=1014,
                               input_patterns=list(INPUTS),
                               bank_upper=256, bank_lower=0,
                               mapping='joint upper-source lower mask04'),
                  equations=dict(
                      pc129_low='(~R1lo + R0lo + carry_in) mod 16',
                      pc129_high='(~ROMhi + R1hi + carry_from_low) mod 16',
                      pc129_carry='carry out of PC129 high slice',
                      pc12a_low='(R1lo + R0lo_from_129 + PC129_carry) mod 16',
                      pc12a_y='R1hi concatenated with PC12A low result'),
                  cases=cases,
                  limitations=[
                      'The selected ROM A8 bank and D127 input values are scenario assumptions, not traced Nokia nets.',
                      'The equations cover the reached q3/mask04 split-slice map, not all alternative field maps.',
                      'The short tone and data-prefix fixtures are internal arithmetic tests, not a measured DAC or line output.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
