"""Challenge frozen thirteen-bit Rx with paced controller A4 and A5 TxD."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit156_staged_transfer import THIRTEEN, staged_state
from joint_mask04_12a_modebit97_cover import STEPS
from joint_mask04_12a_ten_bit_product_bound import cube_hit
from joint_mask04_12a_16byte_reverse_handoff import independent_descramble
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive, spectral_peak

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
PACED = RESULTS / 'main-loop-usart-txready-17.json'
GAIN = RESULTS / 'joint-mask04-12a-modebit159-gain085-fixture.json'
COVER = RESULTS / 'joint-mask04-12a-modebit159-revised-cover.json'
GRAPH = RESULTS / 'joint-mask04-12a-modebit159-nominal-diagnosis.json'
BUSES = line.BUSES
OUT = RESULTS / 'joint-mask04-paced-a4-thirteenbit.json'
SELECTOR = '40'
OFFSET = 203
MODE_EDGE = 48
SHIFT = 5


def run(selector=SELECTOR, segment='A4', out=None):
    if selector not in ('40', '60') or segment not in ('A4', 'A5'):
        raise ValueError('unknown controller selector or segment')
    if out is None:
        name = f'joint-mask04-paced-{segment.lower()}-thirteenbit'
        out = RESULTS / f'{name}{"-answer" if selector == "60" else ""}.json'
    delay = 5 if selector == '40' else 18
    paced = json.loads(PACED.read_text())
    cases = [row for row in paced['cases'] if row['selector'] == selector]
    if (len(cases) != 8 or any(not row['joined_dsc_input_match'] or
                              not row['controller_writes_match'] for row in cases)):
        raise ValueError('paced TxD source changed')
    aligned = [row['aligned_dsc_bytes'] for row in cases]
    if any(row != aligned[0] for row in aligned):
        raise ValueError('TxD clock phases give different DSC bytes')
    start = 0 if segment == 'A4' else 8
    offered = [int(value, 16) for value in aligned[0][start:start + 8]]
    if len(offered) != 8:
        raise ValueError('paced segment lacks eight line bytes')
    expected_payload = independent_descramble(offered, delay)
    gain_fixture = json.loads(GAIN.read_text())
    cover = json.loads(COVER.read_text())
    known = {int(value, 16) for value in json.loads(GRAPH.read_text())[
        'joined_phase_graph']['relative_phase']}
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    tx, raw, expected = line.transmitter(
        capturing_execute((frozen.PHASE_VISIT, OFFSET)),
        mapping, base, offered)
    codes = mapped_codes(raw, buses[0])
    tone = spectral_peak([value - 128 for value in codes[64:TONE_END]],
                         lower=100, upper=3500)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], 0.5)
    selected = wave[SILENCE_END + SHIFT:
                    SILENCE_END + SHIFT + handoff.RX_SYMBOLS * 8]
    gain = next(bus['gain'] for case in gain_fixture['cases']
                if case['selector'] == selector
                for bus in case['bus_cases'] if bus['bus_index'] == 0)
    unbounded = [round(value * gain) for value in selected]
    pcm = [max(-127, min(127, value)) for value in unbounded]
    ref_wrong = [index + 1 for index, (got, want) in enumerate(
        zip(receive(pcm), expected[1:])) if got != want]
    late = MODE_EDGE * edge.loopback.VISITS_PER_SYMBOL * 4 + 1
    mode_values = [0x81] * late + [0xA1] * (edge.MODE_READS - late)
    with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)):
        rx, pc_digest, symbols, gate_edges = fresh.execute_case(
            mapping, base, pcm, mode_values)
    symbols = [symbols[index] for index in range(handoff.RX_SYMBOLS)]
    for index, symbol in enumerate(symbols):
        symbol['visits']['46']['mode_bit5'] = int(index >= MODE_EDGE)
    states = [staged_state(symbol) for symbol in symbols]
    if any(state != code(symbol, THIRTEEN)
           for state, symbol in zip(states, symbols)):
        raise ValueError('staged thirteen-bit state differs from direct capture')
    cubes = [next(row['witness_cubes'] for row in cover['bounds']
                  if (row['phase_bit'], row['on_polarity']) == (bit, 1))
             for bit in (0, 1)]

    def phase(state):
        return sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
                   for bit, terms in enumerate(cubes))

    def captured(symbol, variant, covers):
        state = staged_state(symbol)
        return phase(state), 5000, state

    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        with patch.object(serial, 'captured_phase', captured):
            score = serial.replay(dict(
                multi_visit_symbols=symbols, expected_dibits=expected,
                selector=selector,
                offered_line_bytes=[f'{value:02X}' for value in offered]),
                serial.VARIANTS['aligned'], None, inverse, exe)
    paths = (Path(__file__), PACED, GAIN, COVER, GRAPH, BUSES,
             HERE / 'main_loop_usart_txready_17.py',
             HERE / 'joint_mask04_12a_16byte_reverse_handoff.py',
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_12a_mode_fresh_phase120.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py',
             HERE / 'joint_mask04_12a_modebit156_staged_transfer.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment=f'frozen thirteen-bit receive of paced 8031/8251 {segment} TxD',
                  fixture=dict(selector=selector, segment=segment,
                               paced_txd_clock_phases=[row['tx_clock_phase_ticks'] for row in cases],
                               transmitted_line_bytes=[f'{value:02X}' for value in offered],
                               expected_decoded_bytes=[f'{value:02X}' for value in expected_payload],
                               receiver_probe_initial_history='5A1234',
                               carrier_offset=OFFSET, receive_gain_factor=0.85,
                               assumed_mode_edge_symbol=MODE_EDGE,
                               candidate_dac_bus=buses[0], line_filter_Q=0.5,
                               line_shift_samples=SHIFT,
                               controller_probe_sha256=controller_sha),
                  run=dict(tx_trace_sha256=tx['trace_digest'],
                           tx_candidate_samples=len(raw),
                           tone_peak_hz=tone['frequency_hz'],
                           pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                           clipped_samples=sum(abs(value) > 127 for value in unbounded),
                           reference_wrong_indices=ref_wrong,
                           rx_trace_sha256=rx['trace_digest'],
                           rx_pc_sha256=pc_digest, rx_gate_edges=gate_edges,
                           observed_states=len(set(states)),
                           unseen_vs_frozen_159=[f'{value:04X}' for value in
                                                 sorted(set(states) - known)],
                           wrong_dibit_indices=score['wrong_decision_indices'],
                           recovered_line_bytes=score['recovered_line_bytes'],
                           line_exact=score['recovered_matches_offered'],
                           controller_decoded_bytes=[f'{value:02X}' for value in
                                                     score['controller_decoded_bytes']],
                           controller_exact=score['controller_decoded_bytes'] == expected_payload,
                           controller_status_errors=score['controller_errors'],
                           controller_overruns=score['controller_overruns'],
                           minimum_setup_cycles=score['minimum_setup_cycles']),
                  limitations=[
                      'The 8251 transmit model supplies shifted TxD bits from an executed 8031 stream, but TxD-to-D127 pair buffering is assumed.',
                      'Aligned A4/A5 bytes begin at bit 1 of a controller character; decoded bytes use the receiver probe history, not the original controller plaintext.',
                      'The carrier phase poke, DAC/line/ADC path, D3EB mode, thirteen-bit capture and RxD/RxC/SYNDET connections remain assumed.',
                      f'The frozen gate is unchanged for this {segment} stream; the first preamble dibit is supplied rather than recovered.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('paced', segment, selector, 'wrong', score['wrong_decision_indices'],
          'line exact', score['recovered_matches_offered'],
          'controller exact', score['controller_decoded_bytes'] == expected_payload,
          'unseen', report['run']['unseen_vs_frozen_159'], flush=True)
    return report


if __name__ == '__main__':
    for segment in ('A4', 'A5'):
        for selector in ('40', '60'):
            run(selector, segment)
