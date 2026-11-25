"""Test a counter-qualified, parity-decoded USART dibit pulse at D127."""

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
from photo_a1_dynamic_mode_replay import tone_summary
from photo_controller_mode_decode import decode_chip1
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import PHASE_STEPS, transmit

CONTROLLER = HERE / 'results/main-loop-serial.json'
SELECTORS = ('00', '20', '40', '60')
BASE = 0xb0
FIRST_SYMBOLS = 8
VISITS_PER_SYMBOL = 3000
PULSE_VISITS = 4
VISITS_PER_SAMPLE = 375


def dibit_rule(bit0, bit1):
    """Candidate parity of two line bits drives D4; bit1 drives D5."""
    d4_clear = bit0 ^ bit1
    d5_clear = bit1
    return BASE & ~(d4_clear << 4) & ~(d5_clear << 5)


def width_screen():
    rows = []
    for width in range(1, 9):
        offsets = []
        for dibit in range(4):
            offered = dibit_rule(dibit & 1, dibit >> 1)
            offsets.append((width * (offered - BASE)) & 255)
        rows.append(dict(width=width, phase_offsets=offsets,
                         four_quadrants=set(offsets) == {0, 64, 128, 192}))
    if [row['width'] for row in rows if row['four_quadrants']] != [4]:
        raise AssertionError('four-visit quadrature screen changed')
    if rows[3]['phase_offsets'] != [(-16 * value) & 255
                                   for value in PHASE_STEPS]:
        raise AssertionError('inverse Gray phase order changed')
    return rows


def scenario_inputs(dibits):
    values = []
    for dibit in dibits:
        offered = dibit_rule(dibit & 1, dibit >> 1)
        values.extend([offered] * PULSE_VISITS)
        values.extend([BASE] * (VISITS_PER_SYMBOL - PULSE_VISITS))
    return values + [BASE]


def inspect_trace(path, rom, inputs, dibits):
    symbol_count = len(dibits)
    visits = 0
    phase = 3
    step = None
    symbol_ends = []
    samples = []
    pulse_inputs = set()
    with path.open() as stream:
        for line in stream:
            if '"pc": 295' not in line and '"pc": 297' not in line:
                continue
            row = json.loads(line)
            if row['pc'] == 0x127:
                expected = inputs[min(visits, len(inputs) - 1)]
                event = row['external_read']
                if event['visit'] != visits or event['value'] != expected:
                    raise AssertionError(('D127 input mismatch', visits, event))
                step = expected
                if visits % VISITS_PER_SYMBOL < PULSE_VISITS:
                    pulse_inputs.add(expected)
            elif row['pc'] == 0x129:
                if step is None:
                    raise AssertionError('PC129 before PC127')
                phase = (phase + step) & 255
                selected = row['external_read']
                value = rom[256 + phase]
                y = (phase - value) & 255
                if (selected['address'] != 256 + phase or
                        selected['value'] != value or row['alu']['y'] != y):
                    raise AssertionError(('ROM/Y recurrence', visits, row))
                visit = visits + 1
                if visit % VISITS_PER_SYMBOL == 0 and visit <= symbol_count * VISITS_PER_SYMBOL:
                    symbol = visit // VISITS_PER_SYMBOL - 1
                    baseline = (3 + visit * BASE) & 255
                    actual = (phase - baseline) & 255
                    expected = sum(PULSE_VISITS *
                                   (dibit_rule(d & 1, d >> 1) - BASE)
                                   for d in dibits[:symbol + 1]) & 255
                    if actual != expected:
                        raise AssertionError(('symbol phase offset', symbol,
                                              actual, expected))
                    symbol_ends.append(dict(symbol=symbol, dibit=dibits[symbol],
                                            phase=f'{phase:02X}',
                                            cumulative_offset=f'{actual:02X}'))
                if ((visit - 1) % VISITS_PER_SAMPLE == 0 and
                        visit <= symbol_count * VISITS_PER_SYMBOL):
                    samples.append(dict(visit=visit,
                                        symbol=(visit - 1) // VISITS_PER_SYMBOL,
                                        sample_within_symbol=((visit - 1) %
                                                              VISITS_PER_SYMBOL) // VISITS_PER_SAMPLE,
                                        phase=f'{phase:02X}',
                                        dac_code=f"{q_to_dac(y, 'swap_q4_q5'):02X}"))
                visits += 1
    if len(symbol_ends) != symbol_count or visits < symbol_count * VISITS_PER_SYMBOL:
        raise AssertionError(('incomplete symbol stream', visits, symbol_ends))
    for symbol in range(symbol_count):
        steady = [int(row['phase'], 16) for row in samples
                  if row['symbol'] == symbol and row['sample_within_symbol'] > 0]
        if len(steady) != 7 or any((b - a) & 255 != (VISITS_PER_SAMPLE * BASE) & 255
                                  for a, b in zip(steady, steady[1:])):
            raise AssertionError(('carrier step changed within symbol', symbol,
                                  steady))
    return dict(pc129_visits=visits, symbol_ends=symbol_ends,
                first_16_dac_samples=samples[:16],
                dac_samples=len(samples),
                dac_sample_sha256=hashlib.sha256(bytes(
                    int(row['dac_code'], 16) for row in samples)).hexdigest(),
                first_8_symbol_tone_fit=tone_summary([
                    int(row['dac_code'], 16) for row in samples[:FIRST_SYMBOLS * 8]]),
                full_stream_tone_fit=tone_summary([
                    int(row['dac_code'], 16) for row in samples]),
                pulse_d127_values=sorted(f'{value:02X}' for value in pulse_inputs))


def run(out=HERE / 'results/photo-main-dibit-pulse.json'):
    controller = json.loads(CONTROLLER.read_text())
    rows = {row['selector']: row for row in controller['rows']
            if row['selector'] in SELECTORS}
    if set(rows) != set(SELECTORS):
        raise ValueError('controller stream classes changed')
    rom = ROM.read_bytes()
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for selector in SELECTORS:
        row = rows[selector]
        frame = next(bytes.fromhex(value) for state, value in
                     zip(row['states'], row['frames'])
                     if state not in ('A0', 'A1', 'A2'))
        raw_chip1 = frame[2]
        if decode_chip1(raw_chip1) != (1, 1, BASE):
            raise AssertionError(('main frame decode changed', selector,
                                  frame))
        bits = bits_from_bytes(row['line_bytes'])
        dibits = [bits[i] | (bits[i + 1] << 1)
                  for i in range(0, len(bits), 2)]
        symbol_count = len(dibits)
        cycles = (symbol_count * VISITS_PER_SYMBOL + 64) * 4
        inputs = scenario_inputs(dibits)
        scenario = hold_candidate(base)
        scenario['name'] += '; parity-decoded four-visit controller dibit pulses'
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
        scenario['io']['read']['pc_sequences'][str(0x12c)] = [0x7a]
        scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                            str(0x12e): 256}
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            trace = inspect_trace(Path(temporary) / 'trace.jsonl', rom,
                                  inputs, dibits)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['address_counts'].get(0x129) != trace['pc129_visits'] or
                result['address_counts'].get(0x12e, 0) != 0 or
                trace['dac_samples'] != symbol_count * 8 or
                trace['pulse_d127_values'] != ['80', '90', 'A0', 'B0']):
            raise AssertionError(('DSC pulse run stopped', selector))
        cases.append(dict(selector=selector, frame=frame.hex(' ').upper(),
                          first_line_bytes=[f'{v:02X}' for v in row['line_bytes'][:2]],
                          dsc_microinstructions=cycles,
                          all_dibits=dibits,
                          first_8_dibits=dibits[:FIRST_SYMBOLS],
                          reference_8_symbol_tone_fit=tone_summary(
                              transmit(dibits[:FIRST_SYMBOLS])),
                          reference_full_stream_tone_fit=tone_summary(transmit(dibits)),
                          **trace, trace_digest=result['trace_digest']))
    if {d for case in cases for d in case['first_8_dibits']} != set(range(4)):
        raise AssertionError('controller bits did not exercise all dibits')
    paths = [Path(__file__), CONTROLLER, ROM,
             HERE / 'lower_i_command_data_mix.py',
             HERE / 'photo_a1_dynamic_mode_replay.py',
             HERE / 'reference_modem.py',
             HERE / 'photo_controller_mode_decode.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             HERE.parent / 'board/inventory.json',
             HERE.parent / 'board/evidence/front-annotated.jpg',
             HERE.parent / 'board/evidence/back-annotated.jpg']
    report = dict(
        status='candidate parity/counter D127 pulse yields four retained dibit phase offsets in real PROM execution',
        fixture=dict(controller='unchanged 8031 main-loop USART-01 bytes, LSB-first dibits',
                     mode_frame='main data frame chip1 raw A1 decoded to D127 B0',
                     pulse='At each 1200-symbol/s boundary, D127 D4 clear follows bit0 XOR bit1 and D5 clear follows bit1, for four PC127 visits; B0 otherwise.',
                     candidate_parts='Photographed U1 SN74LS280 and U24 74LS161; no signal routes traced.',
                     oscillator_hz=14_400_000,
                     microinstruction_divisor=1,
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     pulse_visits=PULSE_VISITS,
                     sample_gate='one Y129 capture per 375 PC129 visits; Q4/Q5 swap to DAC08'),
        width_screen=width_screen(), cases=cases,
        limitations=['The USART-to-parity/counter route, four-visit pulse, mode decoder, D127 path, DAC bus and capture clock are untraced hypotheses.',
                     'Four visits is the smallest tested pulse yielding quadrature increments; no photographed net proves this width or gate polarity.',
                     'All 24 or 32 dibits from each 12-iteration controller fixture are executed, but this is not a natural-duration call. The waveform is not pulse-shaped or established as the physical line output.',
                     'No 2100-Hz state is combined with the data run, and no receiver or echo-canceller behavior is demonstrated.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-main-dibit-pulse.json')
    args = parser.parse_args()
    for case in run(args.out)['cases']:
        print(case['selector'], len(case['all_dibits']),
              case['pc129_visits'],
              case['full_stream_tone_fit']['peak_hz'],
              case['reference_full_stream_tone_fit']['peak_hz'])
