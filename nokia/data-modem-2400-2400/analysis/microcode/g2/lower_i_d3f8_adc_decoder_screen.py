"""Screen ADC-bit decoders into reversible, held D3F8 code pairs."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from adc_sample_path import DIBITS
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit
from split_slice_probe import split_scenario

HISTORY = HERE / 'results/lower-i-d3f8-held-history.json'
SAMPLE_START = 64
SAMPLES = 32
VISITS_PER_SAMPLE = (188, 187)
EXPECTED_INPUT_VISITS = SAMPLES * sum(VISITS_PER_SAMPLE) // 2
CYCLES = 8 * EXPECTED_INPUT_VISITS + 47
INPUT_PC = 0x3F8


def reversible_pairs(report):
    long = {(int(row['first_byte'], 16), int(row['later_byte'], 16))
            for row in report['cases']
            if row['status'] == 'same PC path and shared input'}
    pairs = sorted((first, later) for first, later in long
                   if first < later and (later, first) in long)
    if len(pairs) != 7:
        raise ValueError(('reversible input-pair set changed', pairs))
    return pairs


def input_stream(adc_samples, low, high, bit, invert):
    values = []
    for index, sample in enumerate(adc_samples):
        selected = ((sample >> bit) & 1) ^ invert
        values.extend([high if selected else low] * VISITS_PER_SAMPLE[index % 2])
    if len(values) != EXPECTED_INPUT_VISITS:
        raise ValueError('ADC hold schedule length changed')
    return values


def scenario_for(base, values):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    for bit in ('7', '0'):
        scenario['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        scenario['inputs']['register_address_bit_overrides']['a'].pop(bit)
    if INPUT_PC in scenario['io']['read']['address']['pcs']:
        scenario['io']['read']['address']['pcs'].remove(INPUT_PC)
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = values
    scenario['io']['read']['evidence'] += (
        '; ADC0800 complementary code bit decoded to a biased two-level D3F8 '
        'input and held 188/187 visits; physical decoder/route untraced')
    return scenario


def run(out=HERE / 'results/lower-i-d3f8-adc-decoder-screen.json'):
    history = json.loads(HISTORY.read_text())
    pairs = reversible_pairs(history)
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference waveform changed')
    adc = [127 - sample for sample in pcm[SAMPLE_START:SAMPLE_START + SAMPLES]]
    if len(adc) != SAMPLES:
        raise ValueError('ADC stimulus window changed')
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    cases = []
    for low, high in pairs:
        for bit in range(8):
            for invert in (0, 1):
                stream = input_stream(adc, low, high, bit, invert)
                result = execute(mapping, scenario_for(base, stream), CYCLES,
                                 mode='integrated', trace_limit=0)
                visits = result['address_counts'].get(INPUT_PC, 0)
                cases.append(dict(low_code=f'{low:02X}', high_code=f'{high:02X}',
                                  adc_bit=bit, invert=bool(invert),
                                  adc_bit_transitions=sum(((a >> bit) & 1) !=
                                                          ((b >> bit) & 1)
                                                          for a, b in zip(adc, adc[1:])),
                                  selected_input_visits_in_prior_constant_fixture=True,
                                  reached_input_visits=visits,
                                  consumed_full_window=visits >= EXPECTED_INPUT_VISITS,
                                  final_pc=f"{result['final_state']['pc']:03X}",
                                  trace_digest=result['trace_digest']))
    full = [row for row in cases if row['consumed_full_window']]
    if len(cases) != 112 or not full:
        raise ValueError(('ADC decoder coverage/no sustained run', len(cases), len(full)))
    paths = [Path(__file__), HISTORY, HERE / 'adc_sample_path.py',
             HERE / 'reference_modem.py', HERE / 'lower_i_prom_data_route.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='continuous complementary-ADC-bit decoders screened through a held D3F8 ROM loop',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0] * 16,
                               source='32 consecutive samples from 100%-rolloff V.26ter-class reference line signal',
                               reference_dibits=DIBITS,
                               reference_sample_window=[SAMPLE_START, SAMPLE_START + SAMPLES],
                               adc_code='127 - signed PCM sample',
                               adc_samples=adc,
                               decoder='D3F8 is one of seven bidirectionally surviving odd-nibble code pairs; choose pair by one ADC output bit, optional inversion; D0 held high',
                               sample_hold_visits=list(VISITS_PER_SAMPLE),
                               assumed_oscillator_hz=14400000,
                               assumed_microinstructions_per_D3F8_visit=8,
                               expected_input_visits=EXPECTED_INPUT_VISITS,
                               cycles_per_run=CYCLES),
                  summary=dict(reversible_pairs=[[f'{a:02X}', f'{b:02X}'] for a, b in pairs],
                               cases=len(cases), full_window_cases=len(full),
                               full_window_by_pair={f'{a:02X}/{b:02X}': sum(
                                   row['consumed_full_window'] for row in cases
                                   if row['low_code'] == f'{a:02X}' and
                                   row['high_code'] == f'{b:02X}')
                                   for a, b in pairs}),
                  cases=cases,
                  limitations=['Only one reference waveform window, one Q/RAM seed and one candidate field mapping are tested.',
                               'The ADC-to-D3F8 bit decoder, D0 bias, sample clock and physical connector route are untraced hypotheses.',
                               'A full input-window visit count does not by itself prove each byte was selected by the ALU; detailed witnesses must verify that.',
                               'No recovered bit or USART receive path is identified; C3 remains open.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-adc-decoder-screen.json')
    args = parser.parse_args()
    print(run(args.out)['summary']['full_window_by_pair'])
