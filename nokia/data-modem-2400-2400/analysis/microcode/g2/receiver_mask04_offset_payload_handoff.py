"""Challenge the frozen ADC-margin PROM readout with scrambled payloads and drift."""

import hashlib
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import receiver_mask04_multivisit_capture as capture_module
from receiver_mask04_adc_margin_selector import PAIRS, PHASES, select
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import controller, frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_frequency_offset import offset_transmit
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from zero_run_detector import CORE, ROM, line_octets

FIXTURES = ((5, -7, 75, 0xA6E5), (18, 7, 165, 0xC214))
DATA_BYTES = 8
DATA_SYMBOLS = 4 * DATA_BYTES
ADC_VISITS = (capture_module.PREAMBLE_SYMBOLS + DATA_SYMBOLS) * \
    capture_module.VISITS_PER_SYMBOL
CYCLES = 32 * ADC_VISITS + 47


def run(out=HERE / 'results/receiver-mask04-offset-payload-handoff.json'):
    primary, alternative = frozen_tables()
    mapping = capture_module.candidate(
        capture_module.mapping_with_upper_source(0, '17.6'),
        capture_module.mapped(capture_module.MAPPINGS['q3']), 4)
    _, base = capture_module.fixture()
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True, capture_output=True, text=True)
        for delay, offset_hz, degrees, seed in FIXTURES:
            generator = random.Random(seed)
            payload = [generator.randrange(1, 256) for _ in range(DATA_BYTES)]
            offered = line_octets(payload, delay)
            data_dibits = dibits_from_bytes(offered)
            dibits = [3] * capture_module.PREAMBLE_SYMBOLS + data_dibits + [0] * 8
            pcm = offset_transmit(dibits, degrees, offset_hz)
            with patch.object(capture_module, 'DATA_SYMBOLS', DATA_SYMBOLS), \
                    patch.object(capture_module, 'ADC_VISITS', ADC_VISITS), \
                    patch.object(capture_module, 'CYCLES', CYCLES), \
                    patch.object(capture_module, 'PHASES', PHASES), \
                    patch.object(capture_module, 'rotated_transmit',
                                 lambda values, angle: offset_transmit(
                                     values, angle, offset_hz)):
                trace = capture_module.capture(mapping, base, degrees, data_dibits)
            symbols = trace['symbols']
            expected = [symbol['dibit'] for symbol in symbols]
            predictions = {}
            for pair in PAIRS:
                pair_symbols = project(symbols, *pair)
                left = decisions(states_from_symbols(pair_symbols), primary)
                right = decisions(alternative_states(pair_symbols), alternative)
                predictions[pair] = consensus(left, right)
            decoded, selected = select(pcm, predictions)
            score = metrics(decoded, expected)
            data_decisions = decoded[capture_module.PREAMBLE_SYMBOLS:]
            recovered = None
            aligned = None
            early = None
            late = None
            wrong_selector = None
            if all(value is not None for value in data_decisions):
                bits = [bit for dibit in data_decisions
                        for bit in (dibit & 1, (dibit >> 1) & 1)]
                recovered = bytes_lsb_first(bits)
                selector = 0x40 if delay == 5 else 0x60
                aligned = controller(exe, delay, selector, 64, recovered)
                early = controller(exe, delay, selector, 63, recovered)
                late = controller(exe, delay, selector, 65, recovered)
                wrong_selector = controller(
                    exe, delay, 0x60 if delay == 5 else 0x40, 64, recovered)
            rows.append(dict(delay=delay, offset_hz=offset_hz, degrees=degrees,
                             seed=seed, payload=[f'{x:02X}' for x in payload],
                             offered_line_bytes=[f'{x:02X}' for x in offered],
                             recovered_line_bytes=([f'{x:02X}' for x in recovered]
                                                   if recovered is not None else None),
                             score=score, selected_pairs=selected,
                             prom_cycles=CYCLES, trace_digest=trace['trace_digest'],
                             adc_stream_sha256=trace['adc_stream_sha256'],
                             aligned=aligned, early=early, late=late,
                             wrong_selector=wrong_selector))
            print(delay, offset_hz, degrees, score,
                  'bytes', recovered == offered if recovered is not None else None,
                  flush=True)
    paths = (Path(__file__), HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_frequency_offset.py',
             HERE / 'receiver_mask04_offset_visit_phase.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py',
             HERE.parents[1] / 'controller_scrambler.py',
             capture_module.MAPPINGS['q3'], ROM,
             HERE.parent / 'assumed/execute.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c',
                                        'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='offset-carrier random-payload PROM-to-controller challenge',
                  fixture=dict(cases=FIXTURES, preamble_symbols=capture_module.PREAMBLE_SYMBOLS,
                               data_bytes=DATA_BYTES, adc_visits=ADC_VISITS,
                               cycles=CYCLES, capture_phases=PHASES, pairs=PAIRS,
                               rule='unchanged ADC-margin selector and frozen decisions',
                               aligned_syndet_bit=64),
                  cases=rows,
                  aggregate=dict(checks=sum(row['score']['checks'] for row in rows),
                                 errors=sum(row['score']['errors'] for row in rows),
                                 unknown=sum(row['score']['unknown'] for row in rows)),
                  limitations=['The ADC route, external selector, latch/serializer, RxD/RxC and SYNDET wires remain untraced.',
                               'The 81-to-A1 frame edge is not driven in this drift fixture.',
                               'The selected carrier offsets, phases and payloads are bounded challenges.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
