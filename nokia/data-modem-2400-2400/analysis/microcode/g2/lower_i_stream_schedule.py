"""Bound controller-bit and ADC-like input schedules at selected D3F8."""

import hashlib
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from adc_sample_path import DIBITS
from controller_bit_dispatch import controller_stream
from execute import execute
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit
from split_slice_probe import split_scenario

SITE = 0x3F8
STREAM_CYCLES = 1580
HOLDS = (1, 2, 4, 8, 16)


def run_case(mapping, base, values, q, cycles):
    scenario = split_scenario(base)
    scenario['initial']['q'] = q
    for bit in ('7', '0'):
        scenario['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        scenario['inputs']['register_address_bit_overrides']['a'].pop(bit)
    scenario['io']['read']['pc_sequences'][str(SITE)] = values
    scenario['io']['read']['evidence'] += (
        '; diagnostic D3F8 stream timing and Q seed; input wiring untraced')
    result = execute(mapping, scenario, cycles, mode='integrated', trace_limit=0)
    if not result['clean']:
        raise ValueError('stream schedule run incomplete')
    return dict(q=q, site_visits=result['address_counts'].get(SITE, 0),
                selected_rom_reads=result['rom_reads']['selected_by_alu'],
                final_pc=f"{result['final_state']['pc']:03X}",
                trace_digest=result['trace_digest'])


def bit_sequence(bits, lane, hold):
    return [1 | (bit << lane) for bit in bits for _ in range(hold)]


def summarize(rows):
    best = max(rows, key=lambda row: (row['site_visits'],
                                      row['selected_rom_reads']))
    return dict(max_site_visits=best['site_visits'],
                best_q=best['q'],
                best_rom_reads=best['selected_rom_reads'],
                visits_by_q=[row['site_visits'] for row in rows],
                final_pc_by_q=[row['final_pc'] for row in rows])


def run(out=HERE/'results/lower-i-stream-schedule.json'):
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')
    _, bits = controller_stream()
    controller = []
    for lane in (1, 2, 3):
        values = bit_sequence(bits, lane, 1)
        seed_rows = [run_case(mapping, base, values, q, STREAM_CYCLES)
                     for q in range(256)]
        low_q_classes = []
        for low in range(16):
            class_rows = [seed_rows[low + 16*high] for high in range(16)]
            metrics = {(row['site_visits'], row['selected_rom_reads'],
                        row['final_pc']) for row in class_rows}
            if len(metrics) != 1:
                raise ValueError('Q low-nibble repetition changed')
            representative = class_rows[0]
            low_q_classes.append(dict(q_low_nibble=low,
                                      site_visits=representative['site_visits'],
                                      selected_rom_reads=representative['selected_rom_reads'],
                                      final_pc=representative['final_pc']))
        if any(row['site_visits'] >= len(values) for row in seed_rows):
            raise ValueError('a one-visit controller seed consumed all bits')
        schedules = []
        for hold in HOLDS[1:]:
            held = bit_sequence(bits, lane, hold)
            cycles = 50 + 8*(len(held)+2)
            rows = [run_case(mapping, base, held, q, cycles)
                    for q in range(16)]
            if any(row['site_visits'] >= len(held) for row in rows):
                raise ValueError('held controller fixture consumed all bits')
            schedules.append(dict(hold_visits_per_bit=hold,
                                  offered_site_values=len(held),
                                  cycles=cycles,
                                  **summarize(rows)))
        controller.append(dict(lane=lane, one_visit_seed_screen=dict(
                                   q_seeds=256,
                                   max_site_visits=max(row['site_visits'] for row in seed_rows),
                                   q_low_nibble_classes=low_q_classes,
                                   all_256_q_share_low_nibble_metrics=True,
                                   full_stream_q=[]),
                               held_schedules=schedules))
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference receive control failed')
    signal = pcm[:128]
    stimuli = dict(adc=[127-sample for sample in signal],
                   inverted=[128+sample for sample in signal])
    adc_cases = []
    for name, values in stimuli.items():
        if not all(0 <= value <= 255 for value in values):
            raise ValueError('reference ADC byte outside range')
        q_cases = []
        for q in (5, 9):
            for order, offered in (('forward', values),
                                   ('reversed', values[::-1])):
                q_cases.append(dict(order=order,
                                    **run_case(mapping, base, offered, q,
                                               STREAM_CYCLES)))
        shifts = []
        for shift in range(128):
            offered = values[shift:] + values[:shift]
            shifts.append(dict(shift=shift, **run_case(mapping, base, offered,
                                                       5, STREAM_CYCLES)))
        best = max(shifts, key=lambda row: row['site_visits'])
        if any(row['site_visits'] >= 128 for row in shifts):
            raise ValueError('forward ADC cyclic shift unexpectedly consumed all bytes')
        adc_cases.append(dict(polarity=name, q_and_order=q_cases,
                              forward_cyclic_shifts=dict(
                                  tested=128, q=5,
                                  max_site_visits=best['site_visits'],
                                  best_shift=best['shift'],
                                  shifts_reaching_128=[],
                                  visits_histogram=dict(sorted(Counter(
                                      row['site_visits'] for row in shifts).items())),
                                  shift_results=shifts)))
    reversed_adc_q5 = next(row for row in adc_cases[0]['q_and_order']
                           if row['q'] == 5 and row['order'] == 'reversed')
    if (reversed_adc_q5['site_visits'] != 133 or
            adc_cases[0]['forward_cyclic_shifts']['max_site_visits'] != 121 or
            adc_cases[1]['forward_cyclic_shifts']['max_site_visits'] != 98):
        raise ValueError('ADC ordering classification changed')
    paths = [Path(__file__), HERE/'lower_i_prom_data_route.py',
             HERE/'lower_i_input_pipeline.py', HERE/'independent_slice_addresses.py',
             HERE/'independent_slice_fields.py', HERE/'split_slice_probe.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo_controller_path.py',
             HERE/'adc_sample_path.py', HERE/'reference_modem.py',
             HERE.parent/'assumed/execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             HERE.parents[2]/'controller-810244e/nokia-modem-other-board-2764.bin']
    report = dict(status='diagnostic D3F8 stream timing, no sustained controller fixture',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               site='D3F8', q_seed_screen=256,
                               controller_bits=len(bits),
                               reference_samples=len(signal),
                               cycles_for_unheld_stream=STREAM_CYCLES),
                  controller=controller,
                  adc_reference=adc_cases,
                  limitations=[
                      'D3F8 source, byte polarity, bit lanes, clock and PROM-data latch wiring are untraced.',
                      'For held controller bits, Q=0–15 is tested; high-nibble equivalence is verified only for one visit per bit.',
                      'A reversed PCM sample order is a diagnostic control, not a physical receive sequence.',
                      'The screen does not identify a recovered bit or a DAC-bound carrier.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['controller']:
        print(row['lane'], row['one_visit_seed_screen']['max_site_visits'],
              [(s['hold_visits_per_bit'], s['max_site_visits'])
               for s in row['held_schedules']])
    for row in report['adc_reference']:
        print(row['polarity'], row['forward_cyclic_shifts']['max_site_visits'])
