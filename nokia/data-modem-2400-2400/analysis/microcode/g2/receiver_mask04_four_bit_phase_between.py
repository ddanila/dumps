"""Challenge the frozen four-bit readout at intermediate carrier angles."""

import hashlib
import json
import random
from pathlib import Path

from receiver_mask04_four_bit_phase import (HERE, DATA_SYMBOLS, candidate,
                                            capture, fixture, input_code,
                                            mapped, mapping_with_upper_source,
                                            MAPPINGS, phases, score)
from common import save

SOURCE = HERE / 'results/receiver-mask04-four-bit-phase.json'
DEGREES = (15, 30, 60, 75, 105, 120, 150, 165)
SEED = 0x726C


def run(out=HERE / 'results/receiver-mask04-four-bit-phase-between.json'):
    frozen = json.loads(SOURCE.read_text())
    if (frozen['fresh_aggregate'] != dict(checks=470, errors=0, unknown=0) or
            frozen['fixture']['fresh_seeds'] != [0x8D31, 0x2B71]):
        raise ValueError('frozen reference changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    rows = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, SEED, middle)
        pairs = [(symbol['row0']['y'], symbol['row3']['y'])
                 for symbol in case['symbols']]
        y3f8 = [symbol['at_3f8']['y'] for symbol in case['symbols']]
        codes = [input_code(pair[0], y) for pair, y in zip(pairs, y3f8)]
        states = phases(pairs, y3f8)
        result = score(states, [symbol['dibit'] for symbol in case['symbols']])
        rows.append(dict(degrees=degrees, seed=SEED,
                         trace_digest=case['trace_digest'],
                         adc_stream_sha256=case['adc_stream_sha256'],
                         capture_edges=case['gate_edges'],
                         input_codes=codes, phases=states,
                         previously_unseen_codes=sorted(set(codes) -
                                                        {int(key, 2) for key in
                                                         frozen['rule']['phase_by_input']}),
                         score=result,
                         nominal_readout=case['nominal']['all_data'],
                         diagonal_readout=case['diagonal']['all_data']))
        print('captured', degrees, result['errors'], result['unknown'],
              result['unrecognized_symbols'], flush=True)
    paths = [Path(__file__), SOURCE,
             HERE / 'receiver_mask04_four_bit_phase.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='intermediate carrier-angle challenge for frozen four-bit phase readout',
                  fixture=dict(degrees=DEGREES, seed=SEED,
                               data_dibits=middle,
                               rule='unchanged seven-entry row0 Y / 3F8 Y7 table',
                               receiver='continuous 32-symbol preamble plus 16-symbol data real-PROM path'),
                  cases=rows,
                  aggregate=dict(checks=sum(row['score']['checks'] for row in rows),
                                 errors=sum(row['score']['errors'] for row in rows),
                                 unknown=sum(row['score']['unknown'] for row in rows)),
                  limitations=['Intermediate carrier angles test the fixed table only; the ADC, latches, logic, serial clock and RxD route remain assumptions.',
                               'One fresh data stream at eight angles does not establish tolerance to noise or gain changes.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
