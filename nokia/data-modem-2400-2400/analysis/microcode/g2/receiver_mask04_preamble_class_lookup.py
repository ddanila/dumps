"""Challenge a four-code preamble readout selector at new carrier angles."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_preamble_selector import (DATA_SYMBOLS, FRESH_SEED, HERE,
                                                analyze, candidate, capture,
                                                fixture, mapped,
                                                mapping_with_upper_source,
                                                MAPPINGS)

PRIOR = HERE / 'results/receiver-mask04-preamble-selector.json'
CLASS_BY_ROW0 = {'FD': 'nominal', 'F2': 'nominal',
                 'F5': 'diagonal', 'F3': 'diagonal'}
HOLDOUT_DEGREES = (180, 225, 270, 315)


def classify(row):
    selected = CLASS_BY_ROW0.get(row['preamble_row0_byte'])
    score = row[selected + '_data'] if selected else None
    return dict(degrees=row['degrees'], seed=row['seed'],
                preamble_row0_byte=row['preamble_row0_byte'],
                selected_readout=selected, selected_data=score,
                nominal_data=row['nominal_data'], diagonal_data=row['diagonal_data'],
                trace_digest=row['trace_digest'])


def run(out=HERE / 'results/receiver-mask04-preamble-class-lookup.json'):
    prior = json.loads(PRIOR.read_text())
    training = [classify(row) for row in prior['fresh']]
    if ([(row['degrees'], row['preamble_row0_byte']) for row in training] !=
            [(0, 'FD'), (45, 'F5'), (90, 'F2'), (135, 'F3')]):
        raise ValueError('phase-class development bytes changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(FRESH_SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    holdout = []
    for degrees in HOLDOUT_DEGREES:
        case = capture(mapping, base, degrees, FRESH_SEED, middle)
        row = classify(analyze(case))
        holdout.append(row)
        print(degrees, row['preamble_row0_byte'], row['selected_readout'],
              row['selected_data']['errors'] if row['selected_data'] else None,
              row['selected_data']['unknown'] if row['selected_data'] else None,
              flush=True)
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_mask04_preamble_selector.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='four-code preamble phase-class selector at unseen angles',
                  rule=CLASS_BY_ROW0,
                  fixture=dict(training_degrees=[0, 45, 90, 135],
                               holdout_degrees=HOLDOUT_DEGREES,
                               seed=FRESH_SEED, preamble_symbol=16,
                               capture_visit=47),
                  training=training, holdout=holdout,
                  limitations=[
                      'The four-value selector was chosen after inspecting the training carrier angles; holdout angles may yield new latch bytes.',
                      'The selector, phase readouts, latches, serial clock and RxD route are external hypotheses.',
                      'The input is a reference waveform under an assumed complementary-ADC route, not measured Nokia line input.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
