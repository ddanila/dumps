"""Replay two real controller frame-bit edges as candidate short D127 pulses."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_command_data_mix import bits_from_bytes
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac
from photo_i0_hold_screen import hold_candidate
from photo_main_dibit_dac_decode import correlation
from photo_main_dibit_pulse import (BASE, VISITS_PER_SAMPLE, VISITS_PER_SYMBOL,
                                    dibit_rule, scenario_inputs)
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CONTROLLER = HERE / 'results/main-loop-long.json'
WINDOW = range(18, 26)
EDGE_WIDTH = 2
SYMBOLS_PER_BYTE = 4


def controller_window():
    report = json.loads(CONTROLLER.read_text())
    row = next(row for row in report['runs'] if row['selector'] == '00')
    steps = row['iterations']
    selected = [steps[index] for index in WINDOW]
    if any(step['state'] != 'B4' or len(step['line_bytes']) != 1
           for step in selected):
        raise ValueError('B4 controller window changed')
    previous = bytes.fromhex(steps[WINDOW.start - 1]['frame'])[2]
    edges = []
    for index, step in zip(WINDOW, selected):
        current = bytes.fromhex(step['frame'])[2]
        if (previous ^ current) & 0x40:
            edges.append(index)
        previous = current
    if edges != [18, 22] or [bytes.fromhex(s['frame'])[2] for s in selected] != [0xC1] * 4 + [0x81] * 4:
        raise ValueError('controller frame-bit edges changed')
    data = [int(step['line_bytes'][0], 16) for step in selected]
    bits = bits_from_bytes(data)
    dibits = [bits[i] | (bits[i + 1] << 1) for i in range(0, len(bits), 2)]
    return selected, data, dibits, [(index - WINDOW.start) * SYMBOLS_PER_BYTE
                                    for index in edges]


def inputs_for(dibits, edge_symbols, pulsed):
    values = scenario_inputs(dibits)
    if pulsed:
        for symbol in edge_symbols:
            for visit in range(EDGE_WIDTH):
                offset = symbol * VISITS_PER_SYMBOL + visit
                values[offset] += 0x40
                if values[offset] > 255:
                    raise ValueError('D127 pulse overflow')
    return values


def inspect(path, rom, inputs, dibits):
    visits = 0
    phase = 3
    step = None
    samples = []
    ends = []
    with path.open() as stream:
        for line in stream:
            if '"pc": 295' not in line and '"pc": 297' not in line:
                continue
            row = json.loads(line)
            if row['pc'] == 0x127:
                event = row['external_read']
                expected = inputs[min(visits, len(inputs) - 1)]
                if event['visit'] != visits or event['value'] != expected:
                    raise ValueError(('D127 input', visits, event, expected))
                step = expected
            else:
                if step is None:
                    raise ValueError('PC129 before PC127')
                phase = (phase + step) & 255
                event = row['external_read']
                value = rom[256 + phase]
                y = (phase - value) & 255
                if (event['address'] != 256 + phase or event['value'] != value
                        or row['alu']['y'] != y):
                    raise ValueError(('ROM/Y recurrence', visits, row))
                visit = visits + 1
                if visit <= len(dibits) * VISITS_PER_SYMBOL:
                    if (visit - 1) % VISITS_PER_SAMPLE == 0:
                        samples.append(q_to_dac(y, 'swap_q4_q5'))
                    if visit % VISITS_PER_SYMBOL == 0:
                        ends.append(phase)
                visits += 1
    if visits < len(dibits) * VISITS_PER_SYMBOL or len(samples) != 8 * len(dibits):
        raise ValueError(('incomplete DSC replay', visits, len(samples)))
    return dict(pc129_visits=visits, symbol_end_phases=ends,
                samples=samples, sample_sha256=hashlib.sha256(bytes(samples)).hexdigest())


def run(out=HERE / 'results/photo-frame-toggle-edge-pulse.json'):
    frames, line_bytes, dibits, edges = controller_window()
    if edges != [0, 16] or len(dibits) != 32:
        raise ValueError('controller-to-symbol alignment changed')
    width_screen = [dict(width=width, phase_shift=(width * 0x40) & 255)
                    for width in range(1, 5)]
    if [row['width'] for row in width_screen if row['phase_shift'] == 128] != [2]:
        raise ValueError('half-turn width changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for pulsed in (False, True):
        values = inputs_for(dibits, edges, pulsed)
        scenario = hold_candidate(base)
        scenario['name'] += '; controller frame-edge pulse' if pulsed else '; fixed frame-bit control'
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = values
        scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
        scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256, str(0x12e): 256}
        cycles = (len(dibits) * VISITS_PER_SYMBOL + 64) * 4
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            trace = inspect(Path(temporary) / 'trace.jsonl', rom, values, dibits)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['address_counts'].get(0x129) != trace['pc129_visits'] or
                result['address_counts'].get(0x12e, 0)):
            raise ValueError(('DSC replay stopped', pulsed))
        cases.append(dict(frame_edges_applied=pulsed,
                          dsc_microinstructions=cycles,
                          pc129_visits=trace['pc129_visits'],
                          symbol_end_phases=[f'{value:02X}' for value in trace['symbol_end_phases']],
                          first_16_dac_codes=[f'{value:02X}' for value in trace['samples'][:16]],
                          dac_sample_sha256=trace['sample_sha256'],
                          trace_digest=result['trace_digest'],
                          samples=trace['samples']))
    fixed, edge = cases
    offsets = [(a - b) & 255 for a, b in zip(
        (int(v, 16) for v in edge['symbol_end_phases']),
        (int(v, 16) for v in fixed['symbol_end_phases']))]
    if offsets != [128] * 16 + [0] * 16:
        raise ValueError(('phase reversal did not persist/cancel', offsets))
    first_block_correlation = correlation(fixed['samples'][:128], edge['samples'][:128])
    if fixed['samples'][129:] != edge['samples'][129:]:
        raise ValueError('waveform did not return to fixed-bit control')
    for case in cases:
        del case['samples']
    paths = [Path(__file__), CONTROLLER, ROM,
             HERE / 'lower_i_command_data_mix.py',
             HERE / 'photo_127_liveness.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py', MAPPINGS['q3'],
             HERE.parent / 'assumed/common.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'board/inventory.json',
             HERE.parent / 'board/evidence/front-annotated.jpg',
             HERE.parent / 'board/evidence/back-annotated.jpg']
    report = dict(status='hypothetical two-visit D127 pulse on two real controller frame-bit edges causes retained half-turns in DSC PROM execution',
                  controller=dict(selector='00', iterations=list(WINDOW),
                                  frames=[row['frame'] for row in frames],
                                  line_bytes=[f'{value:02X}' for value in line_bytes],
                                  dibits=dibits, edge_symbols=edges),
                  fixture=dict(frame_edge_rule='XOR previous/current chip-1 bit 6; at each edge add D127 bit 6 for two PC127 visits',
                               data_rule='four-visit parity-decoded USART dibit pulses from earlier experiment',
                               bits_per_symbol=2, visits_per_symbol=VISITS_PER_SYMBOL,
                               visits_per_sample=VISITS_PER_SAMPLE,
                               sample_hz=9600,
                               candidate_dac_bus='ordered Y to LS273; Q4/Q5 swapped at DAC08'),
                  width_screen=width_screen, cases=cases,
                  phase_offset_against_fixed=offsets,
                  first_16_symbol_abs_correlation=round(abs(first_block_correlation), 6),
                  first_16_symbol_signed_correlation=round(first_block_correlation, 6),
                  after_second_edge_identical_samples_from_index=129,
                  limitations=['The edge detector, two-visit counter pulse, frame-to-D127 route, DAC bus and clock are untraced hypotheses.',
                               'The controller fixture forces timer expiry each polling iteration; its frame transitions do not establish natural segment-1 timing.',
                               'This is a diagnostic way to obtain half-turns, not proof that Nokia uses the route or that B4 is segment 1.',
                               'No physical line output or DSC receive/echo behavior is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-frame-toggle-edge-pulse.json')
    args = parser.parse_args()
    report = run(args.out)
    print('edges', report['controller']['edge_symbols'],
          'phase offsets', report['phase_offset_against_fixed'][::4],
          'correlation', report['first_16_symbol_signed_correlation'])
