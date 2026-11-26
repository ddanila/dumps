"""Feed executed candidate transmitter Y7 into the real-PROM receive loop."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_mask04_photo_b5_y7_route import bits_from_packed
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import SEGMENT_SYMBOLS, segment2_from_txd
from receiver_mask04_adc_margin_selector import PAIRS, PHASES, select
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_multivisit_capture import (
    MAPPINGS, candidate, configured, execute, fixture, mapped,
    mapping_with_upper_source,
)
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive

SOURCE = HERE / 'results/joint-mask04-msb-data-phase.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
PREAMBLE = 32
DATA = 31
SYMBOLS = PREAMBLE + DATA
VISITS_PER_SYMBOL = 375
ADC_VISITS = SYMBOLS * VISITS_PER_SYMBOL
CYCLES = 32 * ADC_VISITS + 47


def loopback_pcm(case, tx):
    bits = bits_from_packed(case['sites'][0]['packed_msb_lsb_first_hex'])
    if len(bits) != 832:
        raise ValueError('full PROM Y7 sample count changed')
    codes = [8 * bit for bit in bits]
    gated = codes[:TONE_END] + [4] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([code - 4 for code in gated], 1.0)
    selected = line[SILENCE_END + 6:SILENCE_END + 6 + SYMBOLS * 8]
    if len(selected) != SYMBOLS * 8:
        raise ValueError('aligned loopback waveform too short')
    gain = 110 / max(abs(value) for value in selected)
    pcm = [max(-127, min(127, round(value * gain))) for value in selected]
    expected = [3] * PREAMBLE + segment2_from_txd(tx)[:DATA]
    reference = receive(pcm)
    errors = [index for index, (actual, target) in
              enumerate(zip(reference, expected[1:])) if actual != target]
    return pcm, expected, gain, errors


def capture(mapping, base, pcm, expected):
    samples = [127 - value for value in pcm]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS or not all(0 <= value <= 255 for value in values):
        raise ValueError('ADC schedule or byte range changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    captures = {}
    adc_visits = row_visits = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS or
                result['address_counts'].get(0x3ED) != 4 * ADC_VISITS):
            raise ValueError('receive PROM loop stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if row['pc'] == 0x3F8:
                if row['external_read']['value'] != values[adc_visits]:
                    raise ValueError('ADC value changed')
                symbol, phase = divmod(adc_visits, VISITS_PER_SYMBOL)
                if phase in PHASES:
                    captures[(symbol, phase, 'y3f8')] = row['alu']['y']
                adc_visits += 1
            elif row['pc'] == 0x3ED:
                visit, index = divmod(row_visits, 4)
                symbol, phase = divmod(visit, VISITS_PER_SYMBOL)
                if phase in PHASES and index in (0, 3):
                    captures[(symbol, phase, 'row0' if index == 0 else 'row3')] = row['alu']['y']
                row_visits += 1
    if (adc_visits != ADC_VISITS or row_visits != 4 * ADC_VISITS or
            len(captures) != SYMBOLS * len(PHASES) * 3):
        raise ValueError('capture count changed')
    symbols = [dict(symbol=index, dibit=expected[index],
                    visits={str(phase): {
                        key: captures[(index, phase, key)]
                        for key in ('row0', 'y3f8', 'row3')}
                            for phase in PHASES})
               for index in range(SYMBOLS)]
    return result, values, symbols


def run(out=HERE / 'results/joint-mask04-tx-rx-loopback.json'):
    source = json.loads(SOURCE.read_text())
    txready = json.loads(TXREADY.read_text())
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for case in source['cases']:
        selector = case['selector']
        tx = next(row for row in txready['cases'] if row['selector'] == selector)
        pcm, expected, gain, reference_errors = loopback_pcm(case, tx)
        result, adc, symbols = capture(mapping, base, pcm, expected)
        predictions = {}
        for pair in PAIRS:
            projected = project(symbols, *pair)
            first = decisions(states_from_symbols(projected), primary)
            second = decisions(alternative_states(projected), alternative)
            predictions[pair] = consensus(first, second)
        picked, selected = select(pcm, predictions)
        scores = {f'{a}/{b}': classify(predictions[(a, b)], expected)
                  for a, b in PAIRS}
        margin = classify(picked, expected)
        cases.append(dict(selector=selector, tx_trace_digest=case['trace_digest'],
                          rx_trace_digest=result['trace_digest'],
                          tx_y7_sha256=hashlib.sha256(bytes(
                              bits_from_packed(case['sites'][0]['packed_msb_lsb_first_hex']))).hexdigest(),
                          pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          pcm_gain=gain,
                          reference_errors=reference_errors,
                          frozen_pair_scores=scores,
                          margin_score=margin,
                          expected_dibits=expected,
                          margin_decisions=picked,
                          selected_pairs=selected[1:],
                          first_16_expected=expected[:16],
                          first_16_margin=picked[:16]))
        print(selector, 'reference', len(reference_errors),
              'PROM margin', margin, flush=True)
    for case in cases:
        other = next(row for row in cases if row['selector'] != case['selector'])
        case['opposite_selector_control'] = classify(
            case['margin_decisions'], other['expected_dibits'])
        if case['opposite_selector_control']['errors'] == 0:
            raise ValueError('selector streams did not discriminate')
    paths = (Path(__file__), SOURCE, TXREADY,
             HERE / 'joint_mask04_photo_b5_y7_route.py',
             HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_offset_visit_phase.py',
             HERE / 'photo_joint_line_filter_screen.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='candidate executed Y7 transmitter into real-PROM receiver',
                  fixture=dict(preamble_symbols=PREAMBLE, data_symbols=DATA,
                               receive_cycles=CYCLES, adc_visits=ADC_VISITS,
                               tx_output='saved real-PROM Y7 assigned to DAC08 B5',
                               analog='assumed A2 gate and 1950 Hz Q=1 bandpass',
                               sample_alignment=6,
                               adc='gain to ±110 PCM, complementary byte, 47/46 visits per sample',
                               receiver='frozen three-pair ADC-margin selector'),
                  cases=cases,
                  limitations=[
                      'The transmitter and receiver are separate real-PROM runs joined by hypothetical DAC, analog and ADC connections.',
                      'The 6-sample alignment and gain are declared signal fixtures, not traced hardware timing.',
                      'The frozen decision tables and ADC-margin selector are external readout hypotheses, not demonstrated onboard logic.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
