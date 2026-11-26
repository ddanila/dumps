"""Feed offset PROM receive bits through a paced external-sync controller."""

import hashlib
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import receiver_mask04_multivisit_capture as capture_module
from receiver_mask04_adc_margin_selector import PAIRS, PHASES, select
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import controller, frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_frequency_offset import offset_transmit
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, HISTORY, ROM, line_octets

DATA_BYTES = 8
DATA_SYMBOLS = 4 * DATA_BYTES
CASES = ((5, 75, -7), (5, 75, 7),
         (18, 165, -7), (18, 165, 7))
PULSES = (63, 64, 65, 128)


def run(out=HERE / 'results/receiver-mask04-margin-zero-handoff.json'):
    primary, alternative = frozen_tables()
    mapping = capture_module.candidate(
        capture_module.mapping_with_upper_source(0, '17.6'),
        capture_module.mapped(capture_module.MAPPINGS['q3']), 4)
    _, base = capture_module.fixture()
    adc_visits = (capture_module.PREAMBLE_SYMBOLS + DATA_SYMBOLS) * \
        capture_module.VISITS_PER_SYMBOL
    cycles = 32 * adc_visits + 47
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay, degrees, offset_hz in CASES:
            offered = line_octets([0] * DATA_BYTES, delay)
            middle = dibits_from_bytes(offered)
            if len(middle) != DATA_SYMBOLS:
                raise ValueError('scrambled line length changed')
            dibits = [3] * capture_module.PREAMBLE_SYMBOLS + middle + [0] * 8
            pcm = offset_transmit(dibits, degrees, offset_hz)
            with patch.object(capture_module, 'DATA_SYMBOLS', DATA_SYMBOLS), \
                    patch.object(capture_module, 'ADC_VISITS', adc_visits), \
                    patch.object(capture_module, 'CYCLES', cycles), \
                    patch.object(capture_module, 'PHASES', PHASES), \
                    patch.object(capture_module, 'rotated_transmit',
                                 lambda values, angle: offset_transmit(
                                     values, angle, offset_hz)):
                trace = capture_module.capture(mapping, base, degrees, middle)
            expected = [symbol['dibit'] for symbol in trace['symbols']]
            predictions = {}
            variants = {}
            for pair in PAIRS:
                symbols = project(trace['symbols'], *pair)
                p = decisions(states_from_symbols(symbols), primary)
                a = decisions(alternative_states(symbols), alternative)
                both = consensus(p, a)
                predictions[pair] = both
                variants[f'{pair[0]}/{pair[1]}'] = classify(both, expected)
            decoded, selected = select(pcm, predictions)
            score = classify(decoded, expected)
            recovered = None
            pulse_cases = []
            opposite = None
            if score['data_errors'] == score['data_unknown'] == 0:
                bits = [bit for dibit in decoded[32:]
                        for bit in (dibit & 1, (dibit >> 1) & 1)]
                recovered = bytes_lsb_first(bits)
                if recovered != offered:
                    raise ValueError('decoded line bytes differ from fixture')
                selector = 0x40 if delay == 5 else 0x60
                pulse_cases = [dict(pulse=pulse,
                                    result=controller(exe, delay, selector,
                                                      pulse, recovered))
                               for pulse in PULSES]
                opposite = controller(exe, delay,
                                      0x60 if selector == 0x40 else 0x40,
                                      64, recovered)
                aligned = pulse_cases[1]['result']
                if (aligned['state'] != 0xB0 or
                        aligned['zero_octets'] != DATA_BYTES or
                        aligned['consumed_bytes'] != recovered or
                        aligned['decoded_bytes'] != [0] * DATA_BYTES or
                        aligned['completed'] != DATA_BYTES or
                        aligned['consumed'] != DATA_BYTES or
                        aligned['errors'] or aligned['overruns'] or
                        any(item['result']['state'] != 0xAF
                            for index, item in enumerate(pulse_cases)
                            if index != 1) or
                        opposite['state'] != 0xAF or opposite['errors'] or
                        opposite['overruns']):
                    raise ValueError(('paced receive handoff changed',
                                      delay, degrees, offset_hz))
            row = dict(polynomial_delay=delay, degrees=degrees,
                       offset_hz=offset_hz,
                       trace_digest=trace['trace_digest'],
                       adc_stream_sha256=trace['adc_stream_sha256'],
                       offered_line_bytes=[f'{x:02X}' for x in offered],
                       recovered_line_bytes=([f'{x:02X}' for x in recovered]
                                             if recovered is not None else None),
                       variants=variants, score=score,
                       selected_pair_counts=dict(Counter(selected[1:])),
                       pulse_cases=pulse_cases,
                       opposite_selector=opposite)
            rows.append(row)
            print(delay, degrees, offset_hz, score,
                  'line', row['recovered_line_bytes'],
                  'states', [(x['pulse'], x['result']['state'])
                             for x in pulse_cases], flush=True)
    paths = [Path(__file__),
             HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_frequency_offset.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'receiver_timed_controller_handoff.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py', ROM,
             HERE / 'results/receiver-mask04-four-bit-transition.json',
             HERE / 'results/receiver-mask04-feature-choice.json',
             capture_module.MAPPINGS['q3'],
             *(CORE / name for name in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='offset PROM receive to paced 8251/8031 zero-run handoff',
                  fixture=dict(cases=CASES, preamble_symbols=32,
                               data_symbols=DATA_SYMBOLS, data_bytes=DATA_BYTES,
                               capture_phases=PHASES, pairs=PAIRS,
                               adc_visits=adc_visits, cycles=cycles,
                               controller_bit_ticks=BIT_TICKS,
                               pulse_indices=PULSES,
                               adc='complementary PCM, 47/46 visits per sample',
                               mapping='joint upper-source mask 04'),
                  cases=rows,
                  limitations=[
                      'ADC, symbol capture, margin selector, bit serializer, RxD/RxC and SYNDET routes are explicit board hypotheses.',
                      'The 8251 model covers only external-sync shifting and RxRDY; 8031 mode-0 input and serial completion are synthetic, Timer 1 is disabled.',
                      'PROM and controller runs are sequential, not a simultaneous physical-board co-simulation or a C3 pass.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
