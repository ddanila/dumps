"""Measure the D3A1 byte effect while controller bits enter D38E."""

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
from execute import execute
from controller_bit_dispatch import controller_stream
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from split_slice_probe import split_scenario

CYCLES = 320
SAMPLE_VISIT = 20
ADC_PC = 0x3A1
CONTROLLER_PC = 0x38E


def trace_case(mapping, base, controller_bits, sample):
    scenario = copy.deepcopy(base)
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences'][str(CONTROLLER_PC)] = [
        16*bit for bit in controller_bits]
    scenario['io']['read']['pc_sequences'][str(ADC_PC)] = (
        [0]*SAMPLE_VISIT + [sample] + [0]*(127-SAMPLE_VISIT))
    if ADC_PC in scenario['io']['read']['address']['pcs']:
        scenario['io']['read']['address']['pcs'].remove(ADC_PC)
    scenario['io']['read']['evidence'] += (
        '; diagnostic ADC-like byte at D3A1 while D38E retains controller bits; '
        'both physical sources and clock phases untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('incomplete dual-input execution')
    ram = scenario['initial']['ram'][:]
    snapshots = []
    adc_selected = 0
    controller_selected = 0
    output = []
    rom_addresses = []
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] == ADC_PC:
            adc_selected += bool(row['external_read']['selected_by_alu'])
            snapshots.append(dict(ram=ram[:], q=row['q'], alu=row['alu'],
                                  next_pc=row['next_pc'], stack=row['stack_after']))
        if row['pc'] == CONTROLLER_PC:
            controller_selected += bool(row['external_read']['selected_by_alu'])
        if 0x392 <= row['pc'] < 0x3A0:
            output.append((row['pc'], row['alu']['y']))
        event = row['external_read']
        if event.get('selected_by_alu') and 'address' in event:
            rom_addresses.append((row['pc'], event['address']))
    if len(snapshots) <= SAMPLE_VISIT+2:
        raise ValueError('sample and next loop boundary not reached')
    return dict(pcs=[row['pc'] for row in trace],
                snapshots=snapshots, output=output,
                rom_addresses=rom_addresses,
                adc_selected=adc_selected,
                controller_selected=controller_selected,
                trace_digest=result['trace_digest'])


def run(out=HERE/'results/dual-input-adc-nibble.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    cases = []
    for source in (0, 4):
        mapping = mapping_with_source(2, source)
        baseline = trace_case(mapping, scenario, bits, 0)
        values = []
        for sample in range(256):
            row = baseline if sample == 0 else trace_case(
                mapping, scenario, bits, sample)
            if (len(row['snapshots']) != len(baseline['snapshots']) or
                    row['pcs'] != baseline['pcs'] or
                    row['adc_selected'] != baseline['adc_selected'] or
                    row['controller_selected'] != baseline['controller_selected'] or
                    row['output'] != baseline['output'] or
                    row['rom_addresses'] != baseline['rom_addresses'] or
                    row['snapshots'][SAMPLE_VISIT+1:] !=
                    baseline['snapshots'][SAMPLE_VISIT+1:]):
                raise ValueError(f'U11.{source} ADC={sample:02X}: path retained or output changed')
            expected = 0x60 | ((0x0B + (sample & 0x0F)) & 0x0F)
            observed = row['snapshots'][SAMPLE_VISIT]['ram'][7]
            if observed != expected:
                raise ValueError(f'U11.{source} ADC={sample:02X}: R7 rule changed')
            values.append(dict(byte=sample, r7_at_sample=observed,
                               y_at_sample=row['snapshots'][SAMPLE_VISIT]['alu']['y'],
                               trace_digest=row['trace_digest']))
        if baseline['adc_selected'] < SAMPLE_VISIT+3 or baseline['controller_selected'] < SAMPLE_VISIT+3:
            raise ValueError('both inputs were not selected')
        cases.append(dict(lower_i2_source=f'11.{source}', byte_cases=256,
                          adc_selected_within_window=baseline['adc_selected'],
                          controller_selected_within_window=baseline['controller_selected'],
                          r7_by_low_nibble=[values[n]['r7_at_sample'] for n in range(16)],
                          upper_nibble_independent=True,
                          r7_rule='0x60 | ((0x0B + (D3A1 & 0x0F)) & 0x0F)',
                          next_boundary_r7=baseline['snapshots'][SAMPLE_VISIT+1]['ram'][7],
                          all_next_and_later_boundaries_match_zero=True,
                          all_candidate_output_events_match_zero=True,
                          all_selected_rom_addresses_match_zero=True,
                          observation_digest=hashlib.sha256(json.dumps(
                              values, sort_keys=True).encode()).hexdigest(),
                          example_bytes=[values[n] for n in (0,1,5,15,16,127,128,254,255)]))
    paths = [Path(__file__), HERE/'lower_i_input_pipeline.py',
             HERE/'upper_i_field_sensitivity.py',
             HERE/'independent_slice_addresses.py',
             HERE/'independent_slice_fields.py', HERE/'split_slice_probe.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo_controller_path.py',
             HERE/'results/photo-b-constraints/q3-photo-swapped.json',
             ASSUMED/'execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='dual-input D3A1 byte arithmetic, not recovered receiver',
                  fixture=dict(mapping='separated slices, upper B, U2 I2 from U11.0 or U11.4',
                               initial_q=5, initial_ram=[0]*16,
                               controller_input='128 scrambler bits on D4 at PC38E',
                               adc_candidate='one byte at visit 20 of PC3A1',
                               tested_bytes=256, cycles_per_run=CYCLES),
                  cases=cases,
                  limitations=[
                      'ADC0800-to-D3A1 and controller-to-D38E are separate untraced input hypotheses.',
                      'The U11 source, U18 upper fan-out, upper B field, clock and DAC route remain assumptions.',
                      'The low-nibble addition is a one-boundary transient; it does not decode samples or produce a line waveform.',
                      'Only Q=5, zero RAM and one controller stream are tested.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['lower_i2_source'], row['r7_by_low_nibble'],
              row['next_boundary_r7'])
