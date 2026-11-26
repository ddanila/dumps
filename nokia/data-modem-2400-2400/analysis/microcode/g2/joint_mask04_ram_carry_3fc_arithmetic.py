"""Audit every training 3FC/3FD split-slice equation and ROM address."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_external_ram_echo_screen as echo
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured

WINDOWS = dict(training=(0, echo.TRAIN_VISITS),
               early=(0, 32 * 375 // 8),
               late=(96 * 375 // 8, echo.TRAIN_VISITS))


def add_byte(d, a, carry):
    low_total = (d & 15) + (a & 15) + carry
    high_total = (d >> 4) + (a >> 4) + (low_total >> 4)
    return (low_total & 15) | ((high_total & 15) << 4)


def rom_word(d, r5, carry):
    low_total = ((~r5) & 15) + carry
    high_total = (d >> 4) + (r5 >> 4) + (low_total >> 4)
    f = (low_total & 15) | ((high_total & 15) << 4)
    y = (r5 & 15) | ((high_total & 15) << 4)
    return f, y


def distributions(counters):
    return {name: {f'{value:02X}': amount for value, amount in sorted(values.items())}
            for name, values in counters.items()}


def run(out=HERE / 'results/joint-mask04-ram-carry-3fc-arithmetic.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    starts = echo.sample_starts()
    cases = []
    for name, prefix in echo.training_inputs().items():
        samples = prefix + [0] * echo.TAIL_SAMPLES
        adc = [value for index, value in enumerate([127 - x for x in samples])
               for _ in range(47 if index % 8 < 7 else 46)]
        scenario = configured(base, adc, 'previous', 'carry', 1)
        scenario.update(external_ram_feedback=True, external_ram_write=True,
                        external_ram_lane='high', external_ram_latch_pc=0x3F9,
                        external_ram_read_pc=0x3FC,
                        external_ram_read_offset=-3,
                        external_ram_write_until=4 * echo.TRAIN_VISITS,
                        external_ram_address_tick_visits=[4 * tick for tick in starts])
        ram = scenario['initial']['ram'][:]
        visit = -1
        pending_y = None
        pending_d = None
        checked = Counter()
        codebook = Counter()
        counts = {window: {field: Counter() for field in
                           ('d3fc', 'r10_pre3fc', 'carry3fc', 'y3fc',
                            'rom_address', 'rom_byte', 'r5_pre3fd',
                            'carry3fd', 'y3fd')}
                  for window in WINDOWS}
        first_noninitial = None
        with tempfile.TemporaryDirectory() as tmp:
            result = execute(mapping, scenario, echo.CYCLES,
                             mode='integrated', out=tmp,
                             trace_limit=32 * echo.TRAIN_VISITS + 47)
            if (not result['clean'] or result['completed_cycles'] != echo.CYCLES or
                    result['address_counts'].get(0x3F8, 0) != echo.VISITS or
                    result['edge_counts'].get('3ed->3ee', 0)):
                raise ValueError(('receive loop changed', name))
            for line in (Path(tmp) / 'trace.jsonl').open():
                row = json.loads(line)
                if row['pc'] == 0x3F8:
                    visit += 1
                if row['pc'] == 0x3FC and 0 <= visit < echo.TRAIN_VISITS:
                    d = row['external_read']['value']
                    r10, r13 = ram[10], ram[13]
                    carry = row['carry_in']
                    y = add_byte(d, r10, carry)
                    expected_r13 = (r13 & 15) | (y & 0xF0)
                    if (row['instruction_i'] != 0x45 or
                            row['instruction_i_high'] != 0xC5 or
                            row['register_address_a'] != 10 or
                            row['register_address_b'] != 13 or
                            not row['external_read'].get('selected_by_alu') or
                            row['alu']['f'] != y or row['alu']['y'] != y or
                            row['registers'] != (
                                {} if r13 == expected_r13 else {'13': expected_r13})):
                        raise ValueError(('3FC equation changed', name,
                                          row['cycle'], d, r10, carry))
                    checked['3fc'] += 1
                    pending_y = y
                    pending_d = d
                    if d != 1 and first_noninitial is None:
                        first_noninitial = dict(cycle=row['cycle'], d=f'{d:02X}',
                                                r10=f'{r10:02X}', carry=carry,
                                                y3fc=f'{y:02X}')
                    for window, (start, stop) in WINDOWS.items():
                        if start <= visit < stop:
                            for field, value in (('d3fc', d),
                                                 ('r10_pre3fc', r10),
                                                 ('carry3fc', carry),
                                                 ('y3fc', y)):
                                counts[window][field][value] += 1
                if row['pc'] == 0x3FD and 0 <= visit < echo.TRAIN_VISITS:
                    if pending_y is None:
                        raise ValueError(('3FD lacks 3FC predecessor', name,
                                          row['cycle']))
                    read = row['external_read']
                    d = read['value']
                    r5, r10 = ram[5], ram[10]
                    carry = row['carry_in']
                    f, y = rom_word(d, r5, carry)
                    expected_r10 = f
                    if (row['instruction_i'] != 0x94 or
                            row['instruction_i_high'] != 0xC5 or
                            row['register_address_a'] != 5 or
                            row['register_address_b'] != 10 or
                            read['address'] != 0x100 + pending_y or
                            not read.get('selected_by_alu') or
                            row['alu']['f'] != f or row['alu']['y'] != y or
                            row['registers'] != (
                                {} if r10 == expected_r10 else {'10': expected_r10})):
                        raise ValueError(('3FD equation changed', name,
                                          row['cycle'], d, r5, carry,
                                          pending_y, row['registers']))
                    checked['3fd'] += 1
                    codebook[(pending_d, pending_y, read['address'], d, y)] += 1
                    pending_y = None
                    pending_d = None
                    for window, (start, stop) in WINDOWS.items():
                        if start <= visit < stop:
                            for field, value in (('rom_address', read['address']),
                                                 ('rom_byte', d),
                                                 ('r5_pre3fd', r5),
                                                 ('carry3fd', carry),
                                                 ('y3fd', y)):
                                counts[window][field][value] += 1
                for address, value in row['registers'].items():
                    ram[int(address)] = value
        if checked != Counter({'3fc': echo.TRAIN_VISITS,
                               '3fd': echo.TRAIN_VISITS}):
            raise ValueError(('wrong training count', name, checked))
        cases.append(dict(stimulus=name,
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          trace_digest=result['trace_digest'],
                          equations_checked=dict(checked),
                          first_noninitial_read=first_noninitial,
                          codebook=[dict(d3fc=f'{d3fc:02X}',
                                         y3fc=f'{y3fc:02X}',
                                         rom_address=f'{address:03X}',
                                         rom_byte=f'{rom_byte:02X}',
                                         y3fd=f'{y3fd:02X}', count=count)
                                    for (d3fc, y3fc, address, rom_byte, y3fd), count
                                    in sorted(codebook.items())],
                          windows={window: distributions(fields)
                                   for window, fields in counts.items()}))
        print(name, dict(checked), flush=True)
    report = dict(experiment='split-slice 3FC to 3FD arithmetic and ROM address audit',
                  fixture=dict(condition='previous carry, polarity 1',
                               route='3F9 Y high nibble -> sample-paced RAM -> -3 sample 3FC D high nibble',
                               trace='all 6,000 training visits at 3FC and 3FD for each input'),
                  cases=cases,
                  limitations=[
                      'The external RAM return and TEST selection are assumed.',
                      'These checked equations do not identify a physical 3FD output latch or analog residual.',
                      'Only the stated four input streams and training window are covered.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
