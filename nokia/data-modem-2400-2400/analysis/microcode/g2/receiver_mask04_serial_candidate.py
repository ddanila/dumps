"""Schedule a hypothetical 8251A RxD stream from executed receive events."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_phase47_logic import phase_quadrant
from receiver_mask04_two_visit_rule import RULE
from reference_modem import QUADRANT_TO_DIBIT

SOURCE = HERE / 'results/receiver-mask04-protocol-preamble.json'
OSCILLATOR_HZ = 14_400_000
BIT_CYCLES = 6000
RXC_SAMPLE_OFFSET = 3000


def decode(case):
    states = []
    for symbol in case['symbols']:
        pair = (symbol['row0']['y'], symbol['row3']['y'])
        if case['degrees'] == 0:
            state = phase_quadrant(*pair)
        else:
            state = RULE.get(pair)
            if pair == (0xF3, 0xF2):
                state = (symbol['at_3f8']['y'] >> 7) & 1
        states.append(state)
    if any(state is None for state in states):
        raise ValueError('selected phase rule left an unknown symbol')
    dibits = [None]
    for symbol in range(1, len(states)):
        dibits.append(QUADRANT_TO_DIBIT[(states[symbol] -
                                        states[symbol - 1] - 2) & 3])
    if dibits[1:] != [symbol['dibit'] for symbol in case['symbols'][1:]]:
        raise ValueError('selected phase rule lost protocol bits')
    return dibits


def bytes_lsb_first(bits):
    if len(bits) % 8:
        raise ValueError('non-whole character bit count')
    return [sum(bits[index + bit] << bit for bit in range(8))
            for index in range(0, len(bits), 8)]


def schedule(case):
    symbols = case['symbols']
    if (len(symbols) != 48 or
            {b['row3']['cycle'] - a['row3']['cycle']
             for a, b in zip(symbols, symbols[1:])} != {12000} or
            {s['at_3f8']['cycle'] - s['row0']['cycle'] for s in symbols} != {13} or
            {s['row3']['cycle'] - s['at_3f8']['cycle'] for s in symbols} != {11}):
        raise ValueError('receive event timing changed')
    dibits = decode(case)
    events = []
    for symbol in symbols[1:]:
        index = symbol['symbol']
        for bit in (0, 1):
            row3_cycle = symbol['row3']['cycle']
            events.append(dict(symbol=index, bit_in_symbol=bit,
                               launch_cycle=row3_cycle + 1 + BIT_CYCLES * bit,
                               rxc_rising_cycle=row3_cycle + RXC_SAMPLE_OFFSET +
                                                BIT_CYCLES * bit,
                               rxd=(dibits[index] >> bit) & 1))
    if ({b['launch_cycle'] - a['launch_cycle']
         for a, b in zip(events, events[1:])} != {BIT_CYCLES} or
            {b['rxc_rising_cycle'] - a['rxc_rising_cycle']
             for a, b in zip(events, events[1:])} != {BIT_CYCLES}):
        raise ValueError('candidate serial bit spacing changed')
    preamble = [event['rxd'] for event in events if event['symbol'] < 32]
    data = [event['rxd'] for event in events if event['symbol'] >= 32]
    if len(preamble) != 62 or any(bit != 1 for bit in preamble) or len(data) != 32:
        raise ValueError('preamble/data serial window changed')
    expected_data = [bit for symbol in symbols[32:] for bit in
                     ((symbol['dibit'] & 1), ((symbol['dibit'] >> 1) & 1))]
    if data != expected_data:
        raise ValueError('candidate RxD data differs from reference dibits')
    return dict(degrees=case['degrees'], seed=case['seed'],
                trace_digest=case['trace_digest'],
                preamble_recovered_bits=len(preamble),
                preamble_all_ones=all(preamble),
                data_bits=len(data),
                data_bytes_if_boundary_at_first_data_symbol=
                    [f'{byte:02X}' for byte in bytes_lsb_first(data)],
                data_bit_sha256=hashlib.sha256(bytes(data)).hexdigest(),
                first_events=events[:6], last_events=events[-6:],
                bit_spacing_cycles=BIT_CYCLES,
                rxc_setup_cycles=RXC_SAMPLE_OFFSET - 1,
                rxc_hold_cycles=BIT_CYCLES + 1 - RXC_SAMPLE_OFFSET)


def run(out=HERE / 'results/receiver-mask04-serial-candidate.json'):
    source = json.loads(SOURCE.read_text())
    cases = [schedule(case) for case in source['cases']]
    paths = (Path(__file__), SOURCE,
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py',
             HERE.parents[2] / 'photos/PXL_20261123_114723348.jpg',
             HERE.parent / 'board/evidence/front-annotated.jpg')
    report = dict(experiment='hypothetical serial RxD/RxC timing from executed 3ED decisions',
                  fixture=dict(oscillator_hz=OSCILLATOR_HZ,
                               assumed_microcycle_per_oscillator_tick=1,
                               rx_bit_cycles=BIT_CYCLES,
                               rxc_rising_offset_cycles=RXC_SAMPLE_OFFSET,
                               bit_rate_if_assumed_clock_hz=OSCILLATOR_HZ // BIT_CYCLES,
                               receiver='Intel 8251A synchronous eight-bit mode CC, RxD pin 3, RxC pin 25; physical route untraced'),
                  cases=cases,
                  limitations=['The oscillator-to-microcycle and RxC divider paths are not traced.',
                               'Bit launch, serialization, differential phase logic, phase-class selection and DSC-to-DSU RxD wire are external hypotheses.',
                               'The repeated-one sync preamble does not by itself establish the actual 8251A character boundary.',
                               'No physical 8251A receive event or controller data read is observed.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
