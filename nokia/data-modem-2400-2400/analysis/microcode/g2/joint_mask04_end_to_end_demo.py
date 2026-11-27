"""One controller-to-line-to-controller real-PROM modem demonstration."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_fresh_controller_payload as controller_source
from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit156_staged_transfer import THIRTEEN, staged_state
from joint_mask04_12a_modebit97_cover import STEPS
from joint_mask04_12a_ten_bit_product_bound import cube_hit
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import SEGMENT_SYMBOLS
from reference_modem import receive, spectral_peak
from zero_run_detector import HISTORY, line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit159-gain085-holdout.json'
RAW = RESULTS / 'joint-mask04-12a-modebit159-gain085-holdout-edge48-203.json'
GAIN = RESULTS / 'joint-mask04-12a-modebit159-gain085-fixture.json'
COVER = RESULTS / 'joint-mask04-12a-modebit159-revised-cover.json'
BUSES = line.BUSES
OUT = RESULTS / 'joint-mask04-end-to-end-demo.json'
SELECTOR = '40'
OFFSET = 203
MODE_EDGE = 48
SHIFT = 5


def rom_scrambled_octets(payload, delay, temporary):
    if (hashlib.sha256(controller_source.CONTROLLER_ROM.read_bytes()).hexdigest()
            != controller_source.CONTROLLER_SHA):
        raise ValueError('8031 controller ROM changed')
    probe = controller_source.ANALYSIS / 'interface_probe.c'
    core = controller_source.CORE
    executable = Path(temporary) / 'controller-tx-probe'
    subprocess.run(['cc', '-O2', '-Wall', '-DSAT_TRACE', '-I', str(core),
                    str(probe), *(str(core / name) for name in
                                  ('core.c', 'opcodes.c', 'disasm.c')),
                    '-o', str(executable)], check=True,
                   capture_output=True, text=True)
    history = HISTORY
    prior = bytearray(6)
    prior[2] = int(delay == 5)
    frames = []
    predicted_histories = []
    for value in payload:
        frame = bytes((history >> 16, (history >> 8) & 255,
                       history & 255, value, 0, 2))
        frames.append(f'scram {frame.hex()} {prior.hex()} 8 0\n')
        history, _ = controller_source.transform(history, value, delay)
        predicted_histories.append(history)
    completed = subprocess.run([
        str(executable), str(controller_source.CONTROLLER_ROM),
        '248', '0', '256', '8192', '113'], input=''.join(frames),
        text=True, capture_output=True, check=True)
    rows = [json.loads(item) for item in completed.stdout.splitlines()]
    if len(rows) != len(payload):
        raise ValueError('8031 transmit scrambler did not return eight bytes')
    wire = []
    for row, expected_history in zip(rows, predicted_histories):
        ram = row['iram']
        actual_history = (ram[0x3F] << 16) | (ram[0x40] << 8) | ram[0x41]
        if row['errors'] or not row['returned'] or actual_history != expected_history:
            raise ValueError('8031 transmit scrambler execution failed')
        wire.append(ram[0x38])
    return wire


def run(out=OUT):
    summary = json.loads(HOLDOUT.read_text())
    saved = next(row for row in json.loads(RAW.read_text())['cases']
                 if row['selector'] == SELECTOR)
    gain_fixture = json.loads(GAIN.read_text())
    cover = json.loads(COVER.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if (summary['fixture']['carrier_offset'] != OFFSET or
            summary['fixture']['gain_factor'] != 0.85 or
            not any(row['mode'] == 'edge48' and row['selector'] == SELECTOR
                    and not row['wrong_decision_indices']
                    for row in summary['cases'])):
        raise ValueError('saved end-to-end fixture changed')
    payload = [int(value, 16) for value in summary['fixture']['payloads'][SELECTOR]]
    offered = line_octets(payload, 5)
    with tempfile.TemporaryDirectory() as temporary:
        rom_offered = rom_scrambled_octets(payload, 5, temporary)
    if rom_offered != offered:
        raise ValueError('ROM-executed 8031 Tx scrambler differs from line fixture')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    tx, raw, expected = line.transmitter(
        capturing_execute((frozen.PHASE_VISIT, OFFSET)),
        mapping, base, offered)
    if (tx['trace_digest'] != saved['tx_trace_digest'] or
            expected != saved['expected_dibits']):
        raise ValueError('transmitter trace or source dibits changed')
    codes = mapped_codes(raw, buses[0])
    tone = spectral_peak([value - 128 for value in codes[64:TONE_END]],
                         lower=100, upper=3500)
    training_end = SILENCE_END + SEGMENT_SYMBOLS * 8
    carrier = spectral_peak([value - 128 for value in codes[
        SILENCE_END:training_end]], lower=100, upper=3500)
    data_peak = spectral_peak([value - 128 for value in codes[
        training_end:training_end + SEGMENT_SYMBOLS * 8]],
        lower=100, upper=3500)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], 0.5)
    selected = wave[SILENCE_END + SHIFT:
                    SILENCE_END + SHIFT + handoff.RX_SYMBOLS * 8]
    gain = next(bus['gain'] for case in gain_fixture['cases']
                if case['selector'] == SELECTOR
                for bus in case['bus_cases'] if bus['bus_index'] == 0)
    unbounded = [round(value * gain) for value in selected]
    pcm = [max(-127, min(127, value)) for value in unbounded]
    pcm_sha = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
    if pcm_sha != saved['pcm_sha256']:
        raise ValueError('modeled line/ADC samples changed')
    reference_wrong = [index + 1 for index, (got, want) in enumerate(
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
    if (rx['trace_digest'] != saved['rx_trace_digest'] or
            pc_digest != saved['pc_digest'] or
            any(state != code(symbol, THIRTEEN)
                for state, symbol in zip(states, symbols))):
        raise ValueError('real-PROM receiver trace or staged capture changed')
    cubes = [next(row['witness_cubes'] for row in cover['bounds']
                  if (row['phase_bit'], row['on_polarity']) == (bit, 1))
             for bit in (0, 1)]

    def phase(state):
        return sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
                   for bit, terms in enumerate(cubes))

    inverse = {step: dibit for dibit, step in enumerate(STEPS)}

    def captured(symbol, variant, covers):
        return phase(staged_state(symbol)), 5000, staged_state(symbol)

    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        if controller_sha != summary['fixture']['controller_probe_sha256']:
            raise ValueError('8031 probe changed')
        with patch.object(serial, 'captured_phase', captured):
            score = serial.replay(dict(
                multi_visit_symbols=symbols, expected_dibits=expected,
                selector=SELECTOR,
                offered_line_bytes=[f'{value:02X}' for value in offered]),
                serial.VARIANTS['aligned'], None, inverse, exe)
    case_summary = next(row for row in summary['cases']
                        if row['mode'] == 'edge48' and row['selector'] == SELECTOR)
    if (reference_wrong != saved['reference_wrong_indices'] or
            score['wrong_decision_indices'] != case_summary['wrong_decision_indices'] or
            not score['recovered_matches_offered'] or
            score['controller_decoded_bytes'] != payload or
            score['controller_errors'] or score['controller_overruns'] or
            sum(abs(value) > 127 for value in unbounded)):
        raise ValueError('controller-to-controller demonstration changed')
    paths = (Path(__file__), HOLDOUT, RAW, GAIN, COVER, BUSES,
             Path(controller_source.__file__),
             controller_source.CONTROLLER_ROM,
             controller_source.ANALYSIS / 'interface_probe.c',
             controller_source.ANALYSIS / 'controller_scrambler.py',
             *(controller_source.CORE / name for name in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_12a_mode_fresh_phase120.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py',
             HERE / 'joint_mask04_12a_modebit156_staged_transfer.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='one real-PROM controller-to-controller conditional modem demonstration',
                  fixture=dict(selector=SELECTOR, payload=[f'{value:02X}' for value in payload],
                               carrier_offset=OFFSET, gain_factor=0.85,
                               assumed_mode_edge_symbol=MODE_EDGE,
                               candidate_dac_bus=buses[0],
                               line_filter_Q=0.5, line_shift_samples=SHIFT,
                               controller_probe_sha256=controller_sha),
                  chain=dict(
                      rom_executed_8031_scrambler_bytes=[f'{value:02X}' for value in rom_offered],
                      offered_scrambled_line_bytes=[f'{value:02X}' for value in offered],
                      tx_prom_trace_sha256=tx['trace_digest'],
                      tx_12a_samples=len(raw),
                      candidate_dac_codes_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                      modeled_2100hz_tone_peak_hz=tone['frequency_hz'],
                      modeled_segment1_spectrum_peak_hz=carrier['frequency_hz'],
                      modeled_data_spectrum_peak_hz=data_peak['frequency_hz'],
                      pcm_sha256=pcm_sha,
                      clipped_pcm_samples=0,
                      independent_reference_wrong_dibits=reference_wrong,
                      rx_prom_trace_sha256=rx['trace_digest'],
                      rx_pc_trace_sha256=pc_digest,
                      rx_gate_edges=gate_edges,
                      staged_thirteen_bit_states=len(states),
                      wrong_dibit_indices=score['wrong_decision_indices'],
                      recovered_line_bytes=score['recovered_line_bytes'],
                      decoded_controller_bytes=[f'{value:02X}' for value in score['controller_decoded_bytes']],
                      controller_status_errors=score['controller_errors'],
                      minimum_phase_setup_cycles=score['minimum_setup_cycles']),
                  limitations=[
                      'The 8031 scrambler is executed locally for each byte with carried history; a full USART transmit/main-loop run is not modeled.',
                      'The DSC field mapping, controller-to-D127 bit buffering and initial carrier phase poke are conditional model choices.',
                      'DAC08 bit assignment, latch/clock, analog line filter, ADC conversion and gain are assumed, not measured Nokia nets.',
                      'Thirteen-bit capture, phase gates, RxD/RxC/SYNDET and 8251 receive timing are conditional external circuits.',
                      'The first reversal dibit is supplied by the known preamble; subsequent decisions are checked against known transmitted bits.',
                      'This is one full conditional run, not a C2 or C3 physical acceptance pass.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('controller payload', report['fixture']['payload'])
    print('tone peak', tone['frequency_hz'], 'Hz; segment-1 spectrum peak',
          carrier['frequency_hz'], 'Hz; data spectrum peak',
          data_peak['frequency_hz'], 'Hz; Tx samples', len(raw),
          'Rx symbols', len(states), 'wrong dibits', score['wrong_decision_indices'])
    print('decoded controller bytes', report['chain']['decoded_controller_bytes'])
    return report


if __name__ == '__main__':
    run()
