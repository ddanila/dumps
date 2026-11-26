"""Run controller zero bytes through DSC Tx, DSC Rx and paced 8031 handoff."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_four_row_retention_tx import (
    MAPPINGS, candidate, fixture, hold_candidate, mapped,
    mapping_with_upper_source, split_scenario,
)
from joint_mask04_tx_rx_loopback import capture, PREAMBLE, VISITS_PER_SYMBOL as RX_VISITS_PER_SYMBOL
import joint_mask04_tx_rx_loopback as loopback
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
)
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL as TX_VISITS_PER_SYMBOL, scenario_inputs
from receiver_mask04_adc_margin_selector import PAIRS, confidence, select
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import controller, frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive
from zero_run_detector import CORE, HISTORY, ROM, line_octets
from execute import execute

PRIOR_TX = HERE / 'results/joint-mask04-msb-data-phase.json'
DATA_SYMBOLS = 32
SYMBOLS = PREAMBLE + DATA_SYMBOLS
SAMPLES = (TONE_SYMBOLS + SILENCE_SYMBOLS + SYMBOLS) * 8 + 6
TX_CYCLES = (SAMPLES * 375 + 64) * 4
ADC_VISITS = SYMBOLS * RX_VISITS_PER_SYMBOL
RX_CYCLES = 32 * ADC_VISITS + 47


def transmitter(mapping, base, dibits):
    symbols = [3] * SEGMENT_SYMBOLS + dibits
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * TX_VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * TX_VISITS_PER_SYMBOL) +
              scenario_inputs(symbols) + [BASE] * (6 * 375))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; joined controller zero-run with six post-A4 samples'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    bits = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, TX_CYCLES, mode='integrated',
                         out=temporary, trace_limit=TX_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            cycle = row['cycle']
            if cycle < 40 or (cycle - 40) % 1500 or len(bits) >= SAMPLES:
                continue
            if row['pc'] != 0x127:
                raise ValueError(('sample left transmitter loop', cycle, row['pc']))
            bits.append((row['alu']['y'] >> 7) & 1)
    if not result['clean'] or result['completed_cycles'] != TX_CYCLES or len(bits) != SAMPLES:
        raise ValueError(('transmitter did not supply tail samples', len(bits)))
    return result, bits


def pcm_from_bits(bits):
    codes = [8 * bit for bit in bits]
    gated = codes[:TONE_END] + [4] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([code - 4 for code in gated], 1.0)
    selected = line[SILENCE_END + 6:SILENCE_END + 6 + SYMBOLS * 8]
    if len(selected) != SYMBOLS * 8:
        raise ValueError('aligned waveform incomplete')
    gain = 110 / max(abs(value) for value in selected)
    return [max(-127, min(127, round(value * gain))) for value in selected], gain


def run(out=HERE / 'results/joint-mask04-full-zero-handoff.json'):
    prior = json.loads(PRIOR_TX.read_text())
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for selector, delay in (('40', 5), ('60', 18)):
            offered = line_octets([0] * 8, delay)
            dibits = dibits_from_bytes(offered)
            tx_result, bits = transmitter(mapping, base, dibits)
            prior_case = next(c for c in prior['cases'] if c['selector'] == selector)
            prior_bits = loopback.bits_from_packed(
                prior_case['sites'][0]['packed_msb_lsb_first_hex'])
            prefix_length = (TONE_SYMBOLS + SILENCE_SYMBOLS + PREAMBLE) * 8
            prefix_differences = [index for index, (current, previous) in
                                  enumerate(zip(bits[:prefix_length],
                                                prior_bits[:prefix_length]))
                                  if current != previous]
            if prefix_differences:
                raise ValueError(('common A1-A3 transmitter prefix changed',
                                  len(prefix_differences), prefix_differences[:16]))
            pcm, gain = pcm_from_bits(bits)
            expected = [3] * PREAMBLE + dibits
            reference = receive(pcm)
            reference_errors = [i for i, (actual, target) in
                                enumerate(zip(reference, expected[1:]))
                                if actual != target]
            with patch.object(loopback, 'DATA', DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', RX_CYCLES):
                rx_result, adc, symbols = capture(mapping, base, pcm, expected)
            predictions = {}
            for pair in PAIRS:
                projected = project(symbols, *pair)
                first = decisions(states_from_symbols(projected), primary)
                second = decisions(alternative_states(projected), alternative)
                predictions[pair] = consensus(first, second)
            decoded, selected = select(pcm, predictions)
            score = classify(decoded, expected)
            problem_symbols = [dict(
                symbol=index, expected=expected[index],
                selected_pair=selected[index], decoded=decoded[index],
                alternatives={f'{a}/{b}': dict(
                    decision=predictions[(a, b)][index],
                    adc_margin=confidence(pcm, index, (a, b)))
                    for a, b in PAIRS})
                for index in score['wrong_symbols']]
            recovered = None
            handoffs = None
            if score['data_errors'] == score['data_unknown'] == 0:
                recovered = bytes_lsb_first([
                    bit for dibit in decoded[PREAMBLE:]
                    for bit in (dibit & 1, (dibit >> 1) & 1)])
                if recovered != offered:
                    raise ValueError('PROM readout bytes differ from 8031 Tx bytes')
                handoffs = {str(pulse): controller(exe, delay, int(selector, 16),
                                                   pulse, recovered)
                            for pulse in (63, 64, 65, 128)}
                handoffs['opposite_selector'] = controller(
                    exe, delay, 0x60 if selector == '40' else 0x40,
                    64, recovered)
            fixed_decoded = predictions[(46, 93)]
            fixed_score = classify(fixed_decoded, expected)
            fixed_recovered = None
            fixed_handoffs = None
            if fixed_score['data_errors'] == fixed_score['data_unknown'] == 0:
                fixed_recovered = bytes_lsb_first([
                    bit for dibit in fixed_decoded[PREAMBLE:]
                    for bit in (dibit & 1, (dibit >> 1) & 1)])
                if fixed_recovered != offered:
                    raise ValueError('fixed-pair bytes differ from 8031 Tx bytes')
                fixed_handoffs = {str(pulse): controller(
                    exe, delay, int(selector, 16), pulse, fixed_recovered)
                                  for pulse in (63, 64, 65, 128)}
                fixed_handoffs['opposite_selector'] = controller(
                    exe, delay, 0x60 if selector == '40' else 0x40,
                    64, fixed_recovered)
            for label, checked in (('margin', handoffs),
                                   ('fixed 46/93', fixed_handoffs)):
                if checked is not None and (
                        checked['64']['state'] != 0xB0 or
                        checked['64']['zero_octets'] != 8 or
                        checked['64']['decoded_bytes'] != [0] * 8 or
                        any(checked[str(pulse)]['state'] != 0xAF
                            for pulse in (63, 65, 128)) or
                        checked['opposite_selector']['state'] != 0xAF):
                    raise ValueError(('paced handoff control changed',
                                      selector, label))
            rows.append(dict(selector=selector, polynomial_delay=delay,
                             offered_line_bytes=[f'{value:02X}' for value in offered],
                             recovered_line_bytes=([f'{value:02X}' for value in recovered]
                                                   if recovered is not None else None),
                             tx_cycles=tx_result['completed_cycles'],
                             tx_trace_digest=tx_result['trace_digest'],
                             tx_y7_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                             post_a4_bits=bits[-6:], pcm_gain=gain,
                             pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                             rx_cycles=rx_result['completed_cycles'],
                             rx_trace_digest=rx_result['trace_digest'],
                             adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                             reference_errors=reference_errors,
                             score=score,
                             problem_symbols=problem_symbols,
                             fixed_pair_scores={f'{a}/{b}': classify(predictions[(a, b)], expected)
                                                for a, b in PAIRS},
                             fixed_46_93_recovered_line_bytes=(
                                 [f'{value:02X}' for value in fixed_recovered]
                                 if fixed_recovered is not None else None),
                             fixed_46_93_handoffs=fixed_handoffs,
                             selected_pairs=selected[1:],
                             decoded_dibits=decoded,
                             handoffs=handoffs))
            print(selector, 'reference', len(reference_errors),
                  'PROM', score['errors'], score['unknown'],
                  'bytes', recovered == offered if recovered else None,
                  'controller', handoffs['64']['state'] if handoffs else None,
                  flush=True)
    paths = (Path(__file__), PRIOR_TX,
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_pulse.py', ROM,
             MAPPINGS['q3'],
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='controller zero-run through executed DSC transmitter, executed receiver and paced 8031 handoff',
                  fixture=dict(data_bytes=8, preamble_symbols=PREAMBLE,
                               data_symbols=DATA_SYMBOLS, tx_cycles=TX_CYCLES,
                               tx_samples=SAMPLES, rx_cycles=RX_CYCLES,
                               adc_visits=ADC_VISITS,
                               sample_alignment=6,
                               analog='candidate DAC08 B5, A2 gate, Q=1 1950 Hz bandpass, gain to ±110 PCM',
                               adc='complementary PCM, 47/46 visits per sample',
                               receiver='frozen three-pair margin readout',
                               controller='paced external SYNDET 8251/8031 model'),
                  cases=rows,
                  limitations=[
                      'The D127 input and four-visit pulse, DAC and ADC routes, sample clocks, analog filter, receiver readout, RxD/RxC and SYNDET are declared board hypotheses.',
                      'The DSC transmitter, DSC receiver and 8031 controller execute sequentially with modeled handoff; this is not physical-board co-simulation.',
                      'The last six transmitter samples run past the final A4 dibit with D127 held at its baseline value.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
