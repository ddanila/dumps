"""Verify the split-slice arithmetic at the delayed candidate RAM return."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_ram_pulse_freeze as pulse
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

ROUTES = (('01', 3), ('01', 16), ('A1', 3))


def split_f(d, a, carry):
    low_total = (d & 15) + ((~a) & 15) + carry
    low = low_total & 15
    high = ((d >> 4) + (a >> 4) + (low_total >> 4)) & 15
    return low | (high << 4)


def capture(execute, mapping, base, adc, starts, mode, lag):
    scenario = configured(base, adc, 'previous', 'overflow', 1)
    scenario['io']['read']['pc_sequences'][str(0x3EB)] = [int(mode, 16)] * (
        4 * impulse.ADC_VISITS + 1)
    scenario['io']['read']['evidence'] += '; held D3EB mode for RAM arithmetic probe'
    scenario.update(external_ram_feedback=True,
                    external_ram_write=True,
                    external_ram_lane='low',
                    external_ram_latch_pc=0x3F9,
                    external_ram_read_pc=0x3FA,
                    external_ram_read_offset=-lag,
                    external_ram_write_until=pulse.TRAIN_WRITES,
                    external_ram_address_tick_visits=[4 * visit for visit in starts])
    stop_sample = impulse.VARYING_PULSE_SAMPLE + lag + 1
    cycles = 32 * starts[stop_sample] + 47
    target_start = 32 * starts[stop_sample - 1]
    target_stop = 32 * starts[stop_sample] + 47
    rows = []
    ram = scenario['initial']['ram'][:]
    with tempfile.TemporaryDirectory() as tmp:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=tmp, trace_limit=cycles)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['edge_counts'].get('3ed->3ee', 0) != 0 or
                result['external_ram_candidate']['writes'] != pulse.TRAIN_WRITES):
            raise ValueError(('trace stopped', mode, lag))
        for line in (Path(tmp) / 'trace.jsonl').open():
            row = json.loads(line)
            if (row['pc'] == 0x3FA and target_start <= row['cycle'] < target_stop
                    and row['external_read'].get('address') == 26):
                d = row['external_read']['value']
                a = ram[10]
                b = ram[13]
                carry = row['carry_in']
                f = split_f(d, a, carry)
                expected_b = (b & 15) | (f & 0xF0)
                if (row['instruction_i'] != 0x55 or
                        row['instruction_i_high'] != 0xC5 or
                        row['register_address_a'] != 10 or
                        row['register_address_b'] != 13 or
                        not row['external_read'].get('selected_by_alu') or
                        row['alu']['f'] != f or row['alu']['y'] != f or
                        row['registers'] != {'13': expected_b}):
                    raise ValueError(('3FA split equation failed', mode, lag,
                                      row['cycle'], d, a, b))
                rows.append(dict(cycle=row['cycle'], d=d, pre_r10=a,
                                 pre_r13=b, carry=carry, f=f,
                                 post_r13=expected_b, q=row['q']))
            for address, value in row['registers'].items():
                ram[int(address)] = value
    expected_visits = starts[stop_sample] - starts[stop_sample - 1]
    if len(rows) != expected_visits:
        raise ValueError(('delayed read count changed', mode, lag, len(rows)))
    return rows, result


def run(out=HERE / 'results/joint-mask04-ram-return-arithmetic.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if samples[25] != 0x51:
        raise ValueError('reference ADC source changed')
    starts = pulse.sample_starts()
    cases = []
    for mode, lag in ROUTES:
        captured = {}
        for name, changed in (('baseline', None), ('pulse', 0xB1)):
            adc = impulse.held_samples(samples, 25, changed)
            rows, result = capture(execute, mapping, base, adc, starts,
                                   mode, lag)
            captured[name] = rows
            cases.append(dict(mode=mode, lag_samples=lag, input=name,
                              completed_cycles=result['completed_cycles'],
                              trace_digest=result['trace_digest'],
                              row_count=len(rows), first=rows[0],
                              last=rows[-1],
                              distinct={key: sorted({row[key] for row in rows})
                                        for key in ('d', 'pre_r10', 'pre_r13',
                                                    'carry', 'f', 'post_r13', 'q')},
                              row_sha256=hashlib.sha256(bytes(
                                  value for row in rows
                                  for value in (row['d'], row['pre_r10'],
                                                row['pre_r13'], row['carry'],
                                                row['f'], row['post_r13'],
                                                row['q']))).hexdigest()))
            print(mode, lag, name, len(rows), flush=True)
        left, right = captured['baseline'], captured['pulse']
        if any(a['cycle'] != b['cycle'] or a['pre_r10'] != b['pre_r10'] or
               a['pre_r13'] != b['pre_r13'] or a['carry'] != b['carry'] or
               a['post_r13'] != b['post_r13'] or a['q'] != b['q'] or
               a['f'] == b['f'] for a, b in zip(left, right)):
            raise ValueError(('uncontrolled delayed-state difference', mode, lag))
    paths = (Path(__file__), Path(pulse.__file__), Path(impulse.__file__),
             HERE / 'joint_upper_ram_feedback_screen.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE / 'reference_modem.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(
        experiment='split-slice 3FA arithmetic at one delayed hypothetical RAM read',
        fixture=dict(routes=ROUTES, pulse_sample=25, baseline_adc=0x51,
                     pulse_adc=0xB1, train_writes=pulse.TRAIN_WRITES,
                     delayed_address=26, low_instruction='55',
                     high_instruction='C5', source_register=10,
                     destination_register=13),
        equation='low=(Dlo+~R10lo+carry)&15; high=(Dhi+R10hi+low_carry)&15; Y=low|(high<<4); only R13 high nibble written',
        cases=cases,
        limitations=[
            'The RAM return, held D3EB mode, address clock and write gate are hypothetical.',
            'This split operation is not a full-byte subtraction or proof of echo cancellation.',
            'A delayed output byte without a physical consumer is not an identified residual.'
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
