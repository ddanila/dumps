"""Audit 3FA split arithmetic during the sustained high-RAM echo challenge."""

import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_external_ram_echo_screen as prior
from joint_mask04_ram_return_arithmetic import split_f
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured

WINDOWS = {'training': (0, prior.TRAIN_VISITS),
           'early': (0, 32 * 375 // 8),
           'late': (96 * 375 // 8, prior.TRAIN_VISITS)}
FIELDS = ('d', 'r10', 'r13', 'carry', 'y', 'q')


def run(out=HERE / 'results/joint-mask04-ram-carry-arithmetic.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    starts = prior.sample_starts()
    inputs = prior.training_inputs()
    cases = []
    for name, prefix in inputs.items():
        offered = [127 - value for value in prefix + [0] * prior.TAIL_SAMPLES]
        adc = [value for index, value in enumerate(offered)
               for _ in range(47 if index % 8 < 7 else 46)]
        scenario = configured(base, adc, 'previous', 'carry', 1)
        scenario.update(external_ram_feedback=True, external_ram_write=True,
                        external_ram_lane='high', external_ram_latch_pc=0x3F9,
                        external_ram_read_pc=0x3FA,
                        external_ram_read_offset=-3,
                        external_ram_write_until=4 * prior.TRAIN_VISITS,
                        external_ram_address_tick_visits=[4 * tick for tick in starts])
        ram = scenario['initial']['ram'][:]
        visit = -1
        counts = defaultdict(lambda: {field: Counter() for field in FIELDS})
        equations_checked = 0
        r10_changes = 0
        r13_changes = 0
        with tempfile.TemporaryDirectory() as tmp:
            result = execute(mapping, scenario, prior.CYCLES,
                             mode='integrated', out=tmp,
                             trace_limit=32 * prior.TRAIN_VISITS + 47)
            if (not result['clean'] or result['completed_cycles'] != prior.CYCLES or
                    result['address_counts'].get(0x3F8) != prior.VISITS or
                    result['edge_counts'].get('3ed->3ee', 0)):
                raise ValueError(('receive loop changed', name))
            for line in (Path(tmp) / 'trace.jsonl').open():
                row = json.loads(line)
                if row['pc'] == 0x3F8:
                    visit += 1
                if row['pc'] == 0x3FA and 0 <= visit < prior.TRAIN_VISITS:
                    d = row['external_read']['value']
                    r10, r13 = ram[10], ram[13]
                    carry = row['carry_in']
                    y = split_f(d, r10, carry)
                    expected_r13 = (r13 & 15) | (y & 0xF0)
                    if (row['instruction_i'] != 0x55 or
                            row['instruction_i_high'] != 0xC5 or
                            row['register_address_a'] != 10 or
                            row['register_address_b'] != 13 or
                            not row['external_read'].get('selected_by_alu') or
                            row['alu']['f'] != y or row['alu']['y'] != y or
                            row['registers'] != (
                                {} if r13 == expected_r13 else {'13': expected_r13})):
                        raise ValueError(('3FA equation changed', name,
                                          row['cycle'], d, r10, r13, carry))
                    equations_checked += 1
                    for window, (start, stop) in WINDOWS.items():
                        if start <= visit < stop:
                            for field, value in (('d', d), ('r10', r10),
                                                 ('r13', r13), ('carry', carry),
                                                 ('y', y), ('q', row['q'])):
                                counts[window][field][value] += 1
                for address, value in row['registers'].items():
                    if address == '10':
                        r10_changes += 1
                    if address == '13':
                        r13_changes += 1
                    ram[int(address)] = value
        if equations_checked != prior.TRAIN_VISITS:
            raise ValueError(('training 3FA visit count changed', name,
                              equations_checked))
        cases.append(dict(stimulus=name,
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          trace_digest=result['trace_digest'],
                          training_3fa_equations_checked=equations_checked,
                          r10_change_events_in_captured_prefix=r10_changes,
                          r13_change_events_in_captured_prefix=r13_changes,
                          windows={window: {field: {f'{value:02X}': amount
                                                     for value, amount in sorted(values.items())}
                                            for field, values in fields.items()}
                                   for window, fields in counts.items()}))
        print(name, equations_checked, flush=True)
    report = dict(experiment='split-slice 3FA arithmetic under previous-carry high-RAM feedback',
                  fixture=dict(train_samples=prior.TRAIN_SAMPLES,
                               adc_visits=prior.VISITS,
                               cycles=prior.CYCLES,
                               condition='previous carry, polarity 1',
                               output='3FA Y and R13 high-nibble write',
                               equation='low=(Dlo+~R10lo+carry)&15; high=(Dhi+R10hi+low_carry)&15'),
                  cases=cases,
                  limitations=[
                      'The RAM return and TEST selection are hypothetical.',
                      'The captured Y is a mixed-nibble internal code, not measured line echo residual.',
                      'Only early and late training windows are counted; the separate screen checks the frozen tail.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
