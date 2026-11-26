"""Feed two-visit real-PROM receive decisions into the paced 8251/8031 model."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_cubic_transition import fit, forced_prediction
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_feature_choice import alternative_states, development_table
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_protocol_preamble import (MAPPINGS, candidate, configured,
                                               execute, fixture, mapped,
                                               mapping_with_upper_source,
                                               receive, rotated_transmit)
from receiver_mask04_serial_candidate import bytes_lsb_first
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, HISTORY, ROM, line_octets
from receiver_mask04_controller_zero_handoff import dibits_from_bytes

PRIMARY = HERE / 'results/receiver-mask04-four-bit-transition.json'
ALTERNATIVE = HERE / 'results/receiver-mask04-feature-choice.json'
PREAMBLE = 32
DATA_BYTES = 8
VISITS_PER_SYMBOL = 375
ANGLES = ((5, 75), (18, 165))
PULSES = (63, 64, 65, 128)


def capture_zero_stream(mapping, base, degrees, data_dibits):
    dibits = [3] * PREAMBLE + data_dibits + [0] * 8
    symbol_count = PREAMBLE + len(data_dibits)
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost zero-run fixture')
    samples = [127 - value for value in pcm[:8 * symbol_count]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    adc_visits = symbol_count * VISITS_PER_SYMBOL
    cycles = 32 * adc_visits + 47
    if len(values) != adc_visits:
        raise ValueError('ADC hold schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    captures = {}
    adc_event = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['read_sequence_visits'].get(0x3F8) != adc_visits or
                result['address_counts'].get(0x3ED) != 4 * adc_visits):
            raise ValueError('two-visit receive loop stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if row['pc'] != 0x3F8:
                continue
            if (not row['external_read']['selected_by_alu'] or
                    row['external_read']['value'] != values[adc_event]):
                raise ValueError('3F8 ADC input changed')
            symbol, phase = divmod(adc_event, VISITS_PER_SYMBOL)
            if phase in (47, 94):
                captures[(symbol, phase)] = row['alu']['y']
            adc_event += 1
    if adc_event != adc_visits or len(captures) != 2 * symbol_count:
        raise ValueError('two-visit capture count changed')
    symbols = [dict(symbol=index, dibit=dibits[index],
                    visits={str(phase): dict(y3f8=captures[(index, phase)])
                            for phase in (47, 94)})
               for index in range(symbol_count)]
    return dict(degrees=degrees, symbols=symbols,
                trace_digest=result['trace_digest'],
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                cycles=cycles, adc_visits=adc_visits)


def frozen_tables():
    source = json.loads(PRIMARY.read_text())
    alternative_report = json.loads(ALTERNATIVE.read_text())
    if (len(source['rule']['table']) != 86 or
            alternative_report['development']['alternative_keys'] != 91):
        raise ValueError('development readout changed')
    primary = {int(key, 16): value for key, value in
               source['rule']['table'].items()}
    terms, basis, contradictions = fit(primary, 3)
    if contradictions:
        raise ValueError('primary cubic fit changed')
    primary.update({key: value for key in range(256) if key not in primary
                    and (value := forced_prediction(key, terms, basis)) is not None})
    return primary, development_table()


def controller(exe, delay, selector, pulse, values):
    result = subprocess.run(
        [str(exe), str(ROM), str(BIT_TICKS), str(pulse), str(delay),
         str(HISTORY), str(selector), *(str(value) for value in values)],
        capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def run(out=HERE / 'results/receiver-mask04-dual-zero-handoff.json'):
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay, degrees in ANGLES:
            offered = line_octets([0] * DATA_BYTES, delay)
            data_dibits = dibits_from_bytes(offered)
            trace = capture_zero_stream(mapping, base, degrees, data_dibits)
            symbols = trace['symbols']
            expected = [symbol['dibit'] for symbol in symbols]
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            decoded = consensus(p, a)
            scores = dict(primary=metrics(p, expected),
                          alternative=metrics(a, expected),
                          consensus=metrics(decoded, expected))
            conflicts = sum(x is not None and y is not None and x != y
                            for x, y in zip(p[1:], a[1:]))
            recovered = None
            pulse_cases = []
            opposite = None
            if scores['consensus']['errors'] == scores['consensus']['unknown'] == 0:
                bits = [bit for dibit in decoded[PREAMBLE:]
                        for bit in (dibit & 1, (dibit >> 1) & 1)]
                recovered = bytes_lsb_first(bits)
                if (recovered != offered or decoded[1:PREAMBLE] !=
                        [3] * (PREAMBLE - 1)):
                    raise ValueError('recovered line stream differs from fixture')
                selector = 0x40 if delay == 5 else 0x60
                pulse_cases = [dict(pulse=pulse,
                                    result=controller(exe, delay, selector, pulse, recovered))
                               for pulse in PULSES]
                opposite = controller(exe, delay,
                                      0x60 if selector == 0x40 else 0x40,
                                      64, recovered)
                aligned = pulse_cases[1]['result']
                if (aligned['state'] != 0xB0 or aligned['zero_octets'] != DATA_BYTES or
                        aligned['consumed_bytes'] != recovered or
                        aligned['decoded_bytes'] != [0] * DATA_BYTES or
                        aligned['completed'] != DATA_BYTES or
                        aligned['consumed'] != DATA_BYTES or
                        aligned['errors'] or aligned['overruns'] or
                        any(item['result']['state'] != 0xAF
                            for index, item in enumerate(pulse_cases) if index != 1) or
                        opposite['state'] != 0xAF or opposite['errors'] or
                        opposite['overruns']):
                    raise ValueError(('paced zero-run handoff changed', delay,
                                      degrees, pulse_cases, opposite))
            row = dict(polynomial_delay=delay, degrees=degrees,
                       trace_digest=trace['trace_digest'],
                       adc_stream_sha256=trace['adc_stream_sha256'],
                       cycles=trace['cycles'], adc_visits=trace['adc_visits'],
                       offered_line_bytes=[f'{x:02X}' for x in offered],
                       recovered_line_bytes=([f'{x:02X}' for x in recovered]
                                             if recovered is not None else None),
                       scores=scores, conflicts=conflicts,
                       pulse_cases=pulse_cases, opposite_selector=opposite)
            cases.append(row)
            print(delay, degrees, scores, 'conflicts', conflicts,
                  'states', [(x['pulse'], x['result']['state']) for x in pulse_cases],
                  flush=True)
    paths = [Path(__file__), PRIMARY, ALTERNATIVE,
             HERE / 'receiver_mask04_cubic_transition.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'receiver_timed_controller_handoff.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py', ROM, MAPPINGS['q3'],
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             HERE.parents[1] / 'controller_scrambler.py',
             *(CORE / name for name in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='real-PROM dual-feature zero-run receive and paced 8251/8031 handoff',
                  fixture=dict(preamble_symbols=PREAMBLE, data_bytes=DATA_BYTES,
                               degrees=ANGLES, controller_bit_ticks=BIT_TICKS,
                               pulse_indices=PULSES,
                               adc='complementary PCM, 47/46 visits per sample',
                               mapping='joint upper-source mask 04'),
                  cases=cases,
                  limitations=[
                      'The 3F8 ADC ingress, two Y capture clocks, phase logic, serial bit route and external SYNDET source are assumed.',
                      'The 8251 shift/RxRDY model is narrow, the 8031 mode-0 input and serial completion are synthetic, and Timer 1 is disabled.',
                      'This is sequential co-simulation, not simultaneous physical-board execution or a C3 pass.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
