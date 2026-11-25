"""Test held ADC samples at D3A1 while real controller bits occupy D38E."""

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
from adc_sample_path import DIBITS
from lower_i_command_data_mix import bits_from_bytes
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from reference_modem import receive, transmit
from split_slice_probe import split_scenario

CONTROLLER = HERE / 'results/main-loop-long.json'
ADC_PC = 0x3A1
CONTROLLER_PC = 0x38E
VISITS_PER_SAMPLE = 125
VISITS_PER_BIT = 500
PREFIX_SAMPLES = 16
SHARED_SAMPLES = 4
TOTAL_VISITS = (PREFIX_SAMPLES + SHARED_SAMPLES) * VISITS_PER_SAMPLE
CYCLES = TOTAL_VISITS * 12 + 44


def controller_bits():
    report = json.loads(CONTROLLER.read_text())
    row = next(row for row in report['runs'] if row['selector'] == '00')
    line = [int(step['line_bytes'][0], 16) for step in row['iterations'][18:26]]
    bits = bits_from_bytes(line)
    if line != [0xF8, 0x4F, 0x0F, 0x3C, 0x65, 0x08, 0xF5, 0xEC] or bits[:5] != [0, 0, 0, 1, 1]:
        raise ValueError('controller line stream changed')
    return line, bits[:5]


def execute_case(mapping, base, adc_samples, bits, label):
    scenario = split_scenario(base)
    scenario['name'] += f'; held ADC history {label} and line-rate controller bits'
    scenario['initial']['q'] = 5
    adc_stream = [code for sample in adc_samples for code in [sample] * VISITS_PER_SAMPLE]
    controller_stream = [16 * bit for bit in bits for _ in range(VISITS_PER_BIT)]
    scenario['io']['read']['pc_sequences'][str(ADC_PC)] = adc_stream
    scenario['io']['read']['pc_sequences'][str(CONTROLLER_PC)] = controller_stream
    if ADC_PC in scenario['io']['read']['address']['pcs']:
        scenario['io']['read']['address']['pcs'].remove(ADC_PC)
    scenario['io']['read']['evidence'] += (
        '; candidate ADC0800 D3A1 and controller USART D38E routes, held for '
        '125 and 500 loop visits respectively; physical wiring untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        ram = scenario['initial']['ram'][:]
        snapshots = []
        output = []
        rom_reads = []
        adc_values = []
        controller_values = []
        with (Path(temporary) / 'trace.jsonl').open() as stream:
            for line in stream:
                row = json.loads(line)
                for address, value in row['registers'].items():
                    ram[int(address)] = value
                if row['pc'] == ADC_PC:
                    event = row['external_read']
                    if not event['selected_by_alu']:
                        raise ValueError('ADC byte was not selected by ALU')
                    adc_values.append(event['value'])
                    snapshots.append(dict(ram=ram[:], q=row['q'], alu=row['alu'],
                                          next_pc=row['next_pc'], stack=row['stack_after']))
                if row['pc'] == CONTROLLER_PC:
                    event = row['external_read']
                    if not event['selected_by_alu']:
                        raise ValueError('controller bit was not selected by ALU')
                    controller_values.append(event['value'])
                if 0x392 <= row['pc'] < 0x3A0:
                    output.append((row['pc'], row['alu']['y']))
                event = row.get('external_read', {})
                if event.get('selected_by_alu') and 'address' in event:
                    rom_reads.append((row['pc'], event['address']))
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            adc_values != adc_stream or controller_values != controller_stream or
            len(snapshots) != TOTAL_VISITS):
        raise ValueError(('held dual-input run incomplete', label))
    return dict(snapshots=snapshots, output=output, rom_reads=rom_reads,
                final_state=result['final_state'], trace_digest=result['trace_digest'],
                adc_selected=len(adc_values), controller_selected=len(controller_values))


def run(out=HERE / 'results/adc-3a1-held-dual-input.json'):
    line, bits = controller_bits()
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference waveform not decodable')
    complement = [127 - sample for sample in pcm]
    prefix = complement[64:64 + PREFIX_SAMPLES]
    shared = complement[80:80 + SHARED_SAMPLES]
    if prefix == prefix[::-1]:
        raise ValueError('ADC histories did not differ')
    _, base = fixture()
    cases = []
    for source in (0, 4):
        mapping = mapping_with_source(2, source)
        forward = execute_case(mapping, base, prefix + shared, bits, 'forward')
        reverse = execute_case(mapping, base, prefix[::-1] + shared, bits, 'reverse')
        differences = [index for index, (left, right) in enumerate(zip(
            forward['snapshots'], reverse['snapshots'])) if left != right]
        first_shared = PREFIX_SAMPLES * VISITS_PER_SAMPLE
        if (not differences or max(differences) >= first_shared or
                forward['output'] != reverse['output'] or
                forward['rom_reads'] != reverse['rom_reads'] or
                forward['final_state'] != reverse['final_state']):
            raise ValueError(('held ADC history persists', source,
                              differences[-10:]))
        cases.append(dict(lower_i2_source=f'11.{source}',
                          microinstructions_per_run=CYCLES,
                          adc_selected_per_run=forward['adc_selected'],
                          controller_selected_per_run=forward['controller_selected'],
                          differing_adc_boundary_count=len(differences),
                          last_differing_adc_boundary=max(differences),
                          first_shared_adc_boundary=first_shared,
                          same_output_events=True,
                          output_event_count=len(forward['output']),
                          same_selected_rom_addresses=True,
                          selected_rom_reads=len(forward['rom_reads']),
                          same_final_state=True,
                          trace_digests=dict(forward=forward['trace_digest'],
                                             reverse=reverse['trace_digest'])))
    paths = [Path(__file__), CONTROLLER,
             HERE / 'adc_sample_path.py',
             HERE / 'lower_i_command_data_mix.py',
             HERE / 'lower_i_input_pipeline.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE / 'ADC0800-INPUT.md',
             ASSUMED / 'execute.py']
    report = dict(status='held ADC samples at simultaneous D3A1 ingress leave no retained modeled receive history',
                  fixture=dict(controller_selector='00', controller_iterations=list(range(18, 26)),
                               controller_line_bytes=[f'{value:02X}' for value in line],
                               controller_bits=bits,
                               controller_bit_value='16 × bit at D38E',
                               controller_hold_visits_per_bit=VISITS_PER_BIT,
                               adc_code='127 - reference signed PCM at D3A1',
                               adc_hold_visits_per_sample=VISITS_PER_SAMPLE,
                               initial_q=5, initial_ram=[0] * 16,
                               assumed_oscillator_hz=14_400_000,
                               assumed_sample_hz=9600,
                               assumed_line_bit_hz=2400,
                               instruction_count_per_site_visit=12,
                               prefix_samples=PREFIX_SAMPLES,
                               shared_tail_samples=SHARED_SAMPLES,
                               forward_sample_codes=prefix + shared,
                               reverse_sample_codes=prefix[::-1] + shared),
                  cases=cases,
                  limitations=['The two physical D-bus routes, U11 instruction bits, clock divisor, ADC reference range and initial Q/RAM are hypotheses.',
                               'Forced controller polling gives the line bytes; the bit-to-site hold schedule is imposed rather than measured.',
                               'The tested 389–3A1 loop shows no recovered bit or persistent receive history; another mapping or path may.',
                               'No ADC-to-USART receive path is identified.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['lower_i2_source'], case['last_differing_adc_boundary'],
              case['first_shared_adc_boundary'], case['output_event_count'])
