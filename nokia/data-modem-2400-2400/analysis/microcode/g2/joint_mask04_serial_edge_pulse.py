"""Test a causal serial-bit-pair and 16-cycle D127 pulse candidate."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_full_zero_handoff as full
from joint_mask04_full_zero_handoff import pcm_from_bits, transmitter
from photo_joint_tone_training_data import SEGMENT_SYMBOLS
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL, dibit_rule, scenario_inputs
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from reference_modem import receive
from zero_run_detector import line_octets

PRIOR = HERE / 'results/joint-mask04-full-zero-handoff.json'
BOARD_INVENTORY = HERE.parent / 'board/inventory.json'
PREAMBLE = SEGMENT_SYMBOLS
DATA_SYMBOLS = 32
SAMPLES_PER_SYMBOL = 8
BIT_VISITS = VISITS_PER_SYMBOL // 2
PULSE_VISITS = 4
SAMPLE_SHIFT = 6


def serial_pulse_inputs(offered):
    bits = [(byte >> bit) & 1 for byte in offered for bit in range(8)]
    if len(bits) != 64 or VISITS_PER_SYMBOL != 2 * BIT_VISITS:
        raise ValueError('serial schedule changed')
    prefix = scenario_inputs([3] * PREAMBLE)[:-1]
    data = [BASE] * (DATA_SYMBOLS * VISITS_PER_SYMBOL)
    dibits = []
    events = []
    for symbol in range(DATA_SYMBOLS):
        first, second = bits[2 * symbol:2 * symbol + 2]
        dibit = first | (second << 1)
        dibits.append(dibit)
        start = symbol * VISITS_PER_SYMBOL + BIT_VISITS
        value = dibit_rule(first, second)
        data[start:start + PULSE_VISITS] = [value] * PULSE_VISITS
        events.append(dict(symbol=symbol, first_bit=first, second_bit=second,
                           pulse_start_visit=start, pulse_visits=PULSE_VISITS,
                           d127=value))
    if dibits != dibits_from_bytes(offered):
        raise ValueError('bit-pair decode changed')
    return prefix + data + [BASE], dibits, events


def aligned_reference_scores(pcm, expected):
    rows = []
    for shift in range(SAMPLES_PER_SYMBOL):
        selected = pcm[shift:]
        selected = selected[:len(selected) // SAMPLES_PER_SYMBOL * SAMPLES_PER_SYMBOL]
        got = receive(selected)
        target = expected[1:len(got) + 1]
        wrong = [index for index, (actual, want) in
                 enumerate(zip(got, target)) if actual != want]
        rows.append(dict(shift=shift, checks=len(got), errors=len(wrong),
                         wrong_indices=wrong))
    return rows


def run(out=HERE / 'results/joint-mask04-serial-edge-pulse.json'):
    prior = json.loads(PRIOR.read_text())
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        inputs, dibits, events = serial_pulse_inputs(offered)
        with patch.object(full, 'scenario_inputs', lambda symbols: inputs):
            result, y7 = transmitter(mapping, base, dibits)
        baseline = next(case for case in prior['cases'] if case['selector'] == selector)
        if result['completed_cycles'] != baseline['tx_cycles']:
            raise ValueError('PROM run length changed')
        pcm, gain = pcm_from_bits(y7)
        expected = [3] * PREAMBLE + dibits
        scores = aligned_reference_scores(pcm, expected)
        cases.append(dict(selector=selector, polynomial_delay=delay,
                          offered_line_bytes=[f'{x:02X}' for x in offered],
                          bit_pair_events=events,
                          tx_cycles=result['completed_cycles'],
                          tx_trace_digest=result['trace_digest'],
                          tx_y7_sha256=hashlib.sha256(bytes(y7)).hexdigest(),
                          differs_from_symbol_start_pulse=sum(
                              a != b for a, b in zip(y7, full_reconstruct_bits(baseline))),
                          pcm_gain=gain,
                          pcm_sha256=hashlib.sha256(bytes(x + 127 for x in pcm)).hexdigest(),
                          reference_scores=scores))
        print(selector, 'fixed shift', SAMPLE_SHIFT,
              scores[SAMPLE_SHIFT]['errors'], '/', scores[SAMPLE_SHIFT]['checks'],
              'best', min(row['errors'] for row in scores), flush=True)
    paths = (Path(__file__), PRIOR, BOARD_INVENTORY,
             HERE / 'joint_mask04_full_zero_handoff.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'reference_modem.py',
             full.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='controller serial bit-pair with second-bit-edge 16-cycle D127 pulse',
                  fixture=dict(bit_rate_hz=2400, symbol_rate_hz=1200,
                               bit_visits=BIT_VISITS,
                               pulse_visits=PULSE_VISITS,
                               pulse_microcycles=PULSE_VISITS * 4,
                               data_pulse_edge='second bit of each pair',
                               preamble='earlier assumed 11 dibit pulse rule',
                               analog='candidate B5, A2 gate and Q=1 filter',
                               sample_shifts=list(range(SAMPLES_PER_SYMBOL))),
                  cases=cases,
                  limitations=[
                      'The serial bit-pair latches, counter clock/clear, D127 mask and A3 preamble source are board hypotheses; the inventory establishes parts, not nets.',
                      'The 16-cycle pulse duration is modeled as four PC127 visits, one assumed oscillator tick per microinstruction.',
                      'The reference receiver is external and does not establish onboard RxD or a physical DAC path.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


def full_reconstruct_bits(baseline):
    """Reconstruct saved symbol-start fixture for a discrimination control."""
    from joint_mask04_full_zero_analog_variants import reconstructed_pcm
    # The prior report stores the executed Y7 hash but not every bit. The
    # verified recurrence is reconstructed independently of this new pulse.
    from photo_joint_tone_training_data import (
        DATA_STEP, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
    )
    offered = line_octets([0] * 8, baseline['polynomial_delay'])
    dibits = dibits_from_bytes(offered)
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs([3] * PREAMBLE + dibits) + [BASE] * (6 * 375))
    phase = 242
    bits = []
    for index, value in enumerate(inputs):
        phase = (phase + value) & 255
        if index % 375 == 0:
            bits.append(phase >> 7)
        if len(bits) == 838:
            break
    if hashlib.sha256(bytes(bits)).hexdigest() != baseline['tx_y7_sha256']:
        raise ValueError('symbol-start control differs from saved real-PROM output')
    return bits


if __name__ == '__main__':
    run()
