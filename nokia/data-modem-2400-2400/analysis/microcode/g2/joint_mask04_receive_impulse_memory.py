"""Measure downstream state after one ADC sample changes then inputs rejoin."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

SAMPLES = 64
PULSE_SAMPLE = 24
BASE_ADC = 0x7F
HIGH_PULSE_ADC = 0xBF
LOW_PULSE_ADC = 0x70
VARYING_DIBITS = (3, 1, 0, 2, 3, 2, 1, 0)
VARYING_PULSE_SAMPLE = 25
VARYING_HIGH_PULSE_ADC = 0xB1
VARYING_LOW_PULSE_ADC = 0x5E
VISITS_PER_SYMBOL = 375
ADC_VISITS = SAMPLES * VISITS_PER_SYMBOL // 8
CYCLES = 32 * ADC_VISITS + 47
CHANNELS = ('y3f8', 'y3f9', 'y3fa', 'y3ed', 'q') + tuple(
    f'r{i}' for i in range(16))


def held_samples(samples, pulse_sample, pulse_adc):
    samples = list(samples)
    if pulse_adc is not None:
        samples[pulse_sample] = pulse_adc
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('held ADC schedule changed')
    return values


def capture(mapping, base, values):
    scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    rows = []
    fields = {}
    last_y3ed = None
    pc_digest = hashlib.sha256()
    adc_visits = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS or
                result['address_counts'].get(0x3FE) != ADC_VISITS):
            raise ValueError('receive loop did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            if pc == 0x3F8:
                if (row['external_read']['value'] != values[adc_visits] or
                        not row['external_read'].get('selected_by_alu')):
                    raise ValueError('ADC selection changed')
                fields['y3f8'] = row['alu']['y']
                adc_visits += 1
            elif pc == 0x3F9:
                fields['y3f9'] = row['alu']['y']
            elif pc == 0x3FA:
                fields['y3fa'] = row['alu']['y']
            elif pc == 0x3ED:
                last_y3ed = row['alu']['y']
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc == 0x3FE:
                if (last_y3ed is None or
                        any(name not in fields for name in ('y3f8', 'y3f9', 'y3fa'))):
                    raise ValueError('incomplete four-row capture')
                rows.append(bytes((fields['y3f8'], fields['y3f9'], fields['y3fa'],
                                   last_y3ed, row['q'], *ram)))
                fields = {}
                last_y3ed = None
    if len(rows) != ADC_VISITS:
        raise ValueError('receive capture count changed')
    return rows, dict(trace_digest=result['trace_digest'],
                      pc_digest=pc_digest.hexdigest(),
                      row_sha256=hashlib.sha256(b''.join(rows)).hexdigest(),
                      completed_cycles=result['completed_cycles'])


def compare(control, changed, pulse_sample):
    first_pulse_visit = sum(47 if index % 8 < 7 else 46
                            for index in range(pulse_sample))
    after_pulse_visit = first_pulse_visit + (47 if pulse_sample % 8 < 7 else 46)
    channels = {}
    for index, name in enumerate(CHANNELS):
        differences = [visit for visit, (a, b) in enumerate(zip(control, changed))
                       if a[index] != b[index]]
        channels[name] = dict(differing_visits=len(differences),
                              first_difference=differences[0] if differences else None,
                              last_difference=differences[-1] if differences else None,
                              differences_after_pulse=sum(visit >= after_pulse_visit
                                                          for visit in differences),
                              last_difference_after_pulse=(
                                  max((visit for visit in differences
                                       if visit >= after_pulse_visit), default=None)))
    return dict(first_pulse_visit=first_pulse_visit,
                after_pulse_visit=after_pulse_visit,
                channels=channels)


def run(out=HERE / 'results/joint-mask04-receive-impulse-memory.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    varying_samples = [127 - value for value in transmit(VARYING_DIBITS)]
    if (len(varying_samples) != SAMPLES or
            varying_samples[VARYING_PULSE_SAMPLE] != 0x51):
        raise ValueError('varying reference stimulus changed')
    fixtures = (
        ('constant', [BASE_ADC] * SAMPLES, PULSE_SAMPLE,
         HIGH_PULSE_ADC, LOW_PULSE_ADC),
        ('varying', varying_samples, VARYING_PULSE_SAMPLE,
         VARYING_HIGH_PULSE_ADC, VARYING_LOW_PULSE_ADC))
    cases = []
    comparisons = {}
    for fixture_name, samples, pulse_sample, high_pulse, low_pulse in fixtures:
        streams = {}
        for name, pulse in (('baseline', None),
                            ('high_nibble_pulse', high_pulse),
                            ('low_nibble_pulse', low_pulse)):
            values = held_samples(samples, pulse_sample, pulse)
            rows, trace = capture(mapping, base, values)
            streams[name] = rows
            cases.append(dict(fixture=fixture_name, name=name,
                              pulse_sample=pulse_sample, pulse_adc=pulse,
                              adc_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                              **trace))
            print(fixture_name, name, trace['trace_digest'], flush=True)
        comparisons[fixture_name] = {
            name: compare(streams['baseline'], streams[name], pulse_sample)
            for name in ('high_nibble_pulse', 'low_nibble_pulse')}
    paths = (Path(__file__), HERE / 'joint_mask04_adc_rom_wrapper_rule.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(
        experiment='mask-04 downstream state response to one held ADC sample perturbation',
        fixture=dict(samples=SAMPLES, pulse_sample=PULSE_SAMPLE,
                     base_adc=BASE_ADC, high_pulse_adc=HIGH_PULSE_ADC,
                     low_pulse_adc=LOW_PULSE_ADC,
                     varying_dibits=VARYING_DIBITS,
                     varying_pulse_sample=VARYING_PULSE_SAMPLE,
                     varying_base_adc=varying_samples[VARYING_PULSE_SAMPLE],
                     varying_high_pulse_adc=VARYING_HIGH_PULSE_ADC,
                     varying_low_pulse_adc=VARYING_LOW_PULSE_ADC,
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     adc_visits=ADC_VISITS, cycles=CYCLES,
                     dispatch='four-row; previous overflow; D3EB=01',
                     mapping='joint upper-source mask 04',
                     channels=CHANNELS),
        cases=cases, comparisons=comparisons,
        limitations=[
            'The constant and reference-waveform ADC inputs isolate state memory; they are not measured line signals.',
            'Two single-sample pulse positions and values do not characterize all receiver modes or inputs.',
            'The ADC path, row dispatch, TEST source and D3EB level are assumed.',
            'A persistent register difference is not yet a decoded bit or an echo-cancellation residual.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
