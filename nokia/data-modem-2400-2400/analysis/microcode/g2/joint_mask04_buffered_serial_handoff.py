"""Run a one-symbol buffered serial decoder through DSC Tx/Rx and 8031."""

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
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_serial_edge_pulse import full_reconstruct_bits
from photo_joint_tone_training_data import SEGMENT_SYMBOLS, TONE_SYMBOLS, SILENCE_SYMBOLS
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL, dibit_rule, scenario_inputs
from receiver_mask04_adc_margin_selector import PAIRS, select
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import controller, frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive
from zero_run_detector import CORE, ROM, line_octets

PRIOR = HERE / 'results/joint-mask04-full-zero-handoff.json'
CONTROLLER_C = HERE / 'receiver_timed_controller_probe.c'
PREAMBLE = SEGMENT_SYMBOLS
DATA_SYMBOLS = 32
PIPELINE_SYMBOLS = 1
RX_SYMBOLS = PREAMBLE + PIPELINE_SYMBOLS + DATA_SYMBOLS
SAMPLES = (TONE_SYMBOLS + SILENCE_SYMBOLS + RX_SYMBOLS) * 8 + 6
TX_CYCLES = (SAMPLES * 375 + 64) * 4
ADC_VISITS = RX_SYMBOLS * 375
RX_CYCLES = 32 * ADC_VISITS + 47
DATA_START_BIT = 2 * (PREAMBLE + PIPELINE_SYMBOLS)
TOTAL_BITS = DATA_START_BIT + 64


def buffered_inputs(offered):
    bits = [(byte >> bit) & 1 for byte in offered for bit in range(8)]
    if len(bits) != 64:
        raise ValueError('line byte count changed')
    prefix = scenario_inputs([3] * PREAMBLE)[:-1]
    data = [BASE] * ((PIPELINE_SYMBOLS + DATA_SYMBOLS) * VISITS_PER_SYMBOL)
    data[:4] = [dibit_rule(1, 1)] * 4
    dibits = []
    events = []
    for symbol in range(DATA_SYMBOLS):
        first, second = bits[2 * symbol:2 * symbol + 2]
        dibit = first | (second << 1)
        dibits.append(dibit)
        pulse_visit = (symbol + 1) * VISITS_PER_SYMBOL
        data[pulse_visit:pulse_visit + 4] = [dibit_rule(first, second)] * 4
        events.append(dict(symbol=symbol, first_bit=first, second_bit=second,
                           second_bit_visit=symbol * VISITS_PER_SYMBOL +
                           VISITS_PER_SYMBOL // 2,
                           pulse_visit=pulse_visit,
                           d127=dibit_rule(first, second)))
    if dibits != dibits_from_bytes(offered):
        raise ValueError('serial pair decoding changed')
    return prefix + data + [BASE], dibits, events


def compiled_controller(temporary):
    source = CONTROLLER_C.read_text()
    replacements = (
        ('index<64?1:(input[(index-64)/8]>>((index-64)%8))&1',
         'index<66?1:(input[(index-66)/8]>>((index-66)%8))&1'),
        ('pulse_bit>128', 'pulse_bit>130'),
        ('(128+10)*bit_ticks', '(130+10)*bit_ticks'),
        ('next_bit<128', 'next_bit<130'),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError(('paced controller probe changed', old))
        source = source.replace(old, new)
    modified = Path(temporary) / 'buffered_controller_probe.c'
    modified.write_text(source)
    exe = Path(temporary) / 'buffered_controller_probe'
    subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                    '-DSAT_TRACE', '-I', str(CORE), str(modified),
                    *(str(CORE / name) for name in
                      ('core.c', 'opcodes.c', 'disasm.c')),
                    '-o', str(exe)], check=True)
    return exe, hashlib.sha256(source.encode()).hexdigest()


def run(out=HERE / 'results/joint-mask04-buffered-serial-handoff.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_source_sha256 = compiled_controller(temporary)
        for selector, delay in (('40', 5), ('60', 18)):
            offered = line_octets([0] * 8, delay)
            inputs, dibits, events = buffered_inputs(offered)
            with patch.object(full, 'scenario_inputs', lambda symbols: inputs), \
                    patch.object(full, 'SAMPLES', SAMPLES), \
                    patch.object(full, 'TX_CYCLES', TX_CYCLES):
                tx_result, y7 = full.transmitter(mapping, base, dibits)
            baseline = next(case for case in prior['cases'] if case['selector'] == selector)
            baseline_y7 = full_reconstruct_bits(baseline)
            prefix = (TONE_SYMBOLS + SILENCE_SYMBOLS + PREAMBLE) * 8
            if y7[:prefix] != baseline_y7[:prefix]:
                raise ValueError('common A1-A3 PROM output changed')
            with patch.object(full, 'SYMBOLS', RX_SYMBOLS):
                pcm, gain = full.pcm_from_bits(y7)
            expected = [3] * (PREAMBLE + PIPELINE_SYMBOLS) + dibits
            reference = receive(pcm)
            reference_errors = [index for index, (actual, want) in
                                enumerate(zip(reference, expected[1:]))
                                if actual != want]
            with patch.object(loopback, 'DATA', PIPELINE_SYMBOLS + DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', RX_CYCLES):
                rx_result, adc, symbols = loopback.capture(mapping, base, pcm, expected)
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
            fixed = predictions[(46, 93)]
            data_decisions = fixed[PREAMBLE + PIPELINE_SYMBOLS:]
            data_wrong = [index for index, (actual, want) in
                          enumerate(zip(data_decisions, dibits))
                          if actual is not None and actual != want]
            data_unknown = [index for index, actual in
                            enumerate(data_decisions) if actual is None]
            recovered = None
            handoffs = None
            if not data_wrong and not data_unknown:
                recovered = bytes_lsb_first([
                    bit for dibit in data_decisions
                    for bit in (dibit & 1, (dibit >> 1) & 1)])
                if recovered != offered:
                    raise ValueError('buffered readout bytes differ from controller source')
                handoffs = {str(pulse): controller(exe, delay, int(selector, 16),
                                                   pulse, recovered)
                            for pulse in (DATA_START_BIT - 1, DATA_START_BIT,
                                          DATA_START_BIT + 1, TOTAL_BITS)}
                handoffs['opposite_selector'] = controller(
                    exe, delay, 0x60 if selector == '40' else 0x40,
                    DATA_START_BIT, recovered)
            cases.append(dict(selector=selector, polynomial_delay=delay,
                              offered_line_bytes=[f'{x:02X}' for x in offered],
                              bit_pair_events=events,
                              tx_cycles=tx_result['completed_cycles'],
                              tx_trace_digest=tx_result['trace_digest'],
                              tx_y7_sha256=hashlib.sha256(bytes(y7)).hexdigest(),
                              common_prefix_samples=prefix,
                              pcm_gain=gain,
                              pcm_sha256=hashlib.sha256(bytes(x + 127 for x in pcm)).hexdigest(),
                              reference_errors=reference_errors,
                              rx_cycles=rx_result['completed_cycles'],
                              rx_trace_digest=rx_result['trace_digest'],
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              fixed_pair_scores=scores,
                              fixed_data_wrong_indices=data_wrong,
                              fixed_data_unknown_indices=data_unknown,
                              margin_score=margin,
                              margin_wrong_pairs=[dict(symbol=index,
                                                       pair=selected[index],
                                                       expected=expected[index],
                                                       actual=picked[index])
                                                  for index in margin['wrong_symbols']],
                              recovered_line_bytes=(
                                  [f'{x:02X}' for x in recovered]
                                  if recovered is not None else None),
                              controller_handoffs=handoffs))
            print(selector, 'reference', len(reference_errors),
                  'fixed data wrong/unknown', len(data_wrong), len(data_unknown),
                  'margin', margin['errors'], margin['unknown'],
                  'controller', handoffs[str(DATA_START_BIT)]['state']
                  if handoffs else None, flush=True)
    paths = (Path(__file__), PRIOR, CONTROLLER_C,
             HERE / 'joint_mask04_full_zero_handoff.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'joint_mask04_serial_edge_pulse.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py', ROM,
             full.MAPPINGS['q3'],
             *(CORE / name for name in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='buffered serial bit-pair pulse through DSC Tx/Rx and paced 8031',
                  fixture=dict(bit_rate_hz=2400, symbol_rate_hz=1200,
                               pipeline_symbols=PIPELINE_SYMBOLS,
                               preamble_symbols=PREAMBLE,
                               data_symbols=DATA_SYMBOLS,
                               tx_samples=SAMPLES, tx_cycles=TX_CYCLES,
                               rx_symbols=RX_SYMBOLS, rx_cycles=RX_CYCLES,
                               adc_visits=ADC_VISITS,
                               data_start_bit=DATA_START_BIT,
                               total_serial_bits=TOTAL_BITS,
                               pulse_width_visits=4,
                               analog='candidate B5, A2 gate, Q=1 filter, six-sample alignment',
                               modified_controller_probe_sha256=controller_source_sha256),
                  cases=cases,
                  limitations=[
                      'The paired-bit latch, 16-cycle counter pulse, D127 mask, DAC/ADC paths, A3 source, sample clocks and external SYNDET route are untraced hypotheses.',
                      'The 8031 probe is the earlier narrow paced 8251 model with its preamble length changed from 64 to 66 bits; processors run sequentially.',
                      'The frozen receive decisions are external diagnostics, not demonstrated onboard gates or USART-01 pins.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
