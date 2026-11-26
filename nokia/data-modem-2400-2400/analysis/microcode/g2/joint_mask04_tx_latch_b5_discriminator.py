"""Predict DAC08 B5 for serial-hold versus shared-Y latch topologies."""

import hashlib
import json
from pathlib import Path

from joint_mask04_tx_bank_phase import scenario_for
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from joint_four_row_retention_tx import (
    BUSES, MAPPINGS, SAMPLE_COUNT, SAMPLE_DIVISOR, TXREADY, candidate,
    fixture, mapped, mapping_with_upper_source,
)
from photo_dac_bus_permutations import mapped_codes
from photo_joint_tone_training_data import (
    SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_SYMBOLS, TOTAL_SYMBOLS,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-tx-12a-delayed-latch.json'
BANK = HERE / 'results/joint-mask04-tx-bank-phase.json'
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'
OUT = HERE / 'results/joint-mask04-tx-latch-b5-discriminator.json'


def segments(a, b):
    boundaries = (('A1_tone', TONE_SYMBOLS * 8),
                  ('A2_silence', SILENCE_SYMBOLS * 8),
                  ('A3_reversals', SEGMENT_SYMBOLS * 8),
                  ('A4_data', SEGMENT_SYMBOLS * 8))
    start = 0
    results = {}
    for label, length in boundaries:
        end = start + length
        results[label] = sum(x != y for x, y in zip(a[start:end], b[start:end]))
        start = end
    if start != SAMPLE_COUNT:
        raise ValueError('controller segment sample count changed')
    return results


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    bank = json.loads(BANK.read_text())
    controller = json.loads(TXREADY.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if (len(buses) != 6 or any(bus[4] != 3 or bus[0] != 4 for bus in buses)):
        raise ValueError('surviving DAC bus bit assignments changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = capturing_execute()
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    cases = []
    for selector in ('40', '60'):
        controller_case = next(x for x in controller['cases'] if x['selector'] == selector)
        result = execute(mapping, scenario_for(base, controller_case, 256),
                         cycles, mode='integrated', trace_limit=0)
        old = next(x for x in prior['cases'] if x['selector'] == selector)
        old_bank = next(x for x in bank['cases'] if x['selector'] == selector)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['trace_digest'] != old['trace_digests']['256'] or
                result['trace_digest'] != old_bank['trace_digests']['256']):
            raise ValueError(('real-PROM controller stream changed', selector))
        first = result['site_y'][0x12A]
        following = result['site_y'][0x127]
        if len(first) != len(following) or len(first) != 312054:
            raise ValueError('loop capture visits changed')
        held = [first[SAMPLE_DIVISOR * n] for n in range(SAMPLE_COUNT)]
        shared = [following[SAMPLE_DIVISOR * n + 1] for n in range(SAMPLE_COUNT)]
        if (hashlib.sha256(bytes(held)).hexdigest() !=
                old['phases'][0]['banks']['256']['raw_y_sha256'] or
                hashlib.sha256(bytes(shared)).hexdigest() !=
                old['phases'][1]['banks']['256']['raw_y_sha256']):
            raise ValueError('topology sample bytes differ from timed-latch replay')
        held_b5 = [(value >> 4) & 1 for value in held]
        shared_b5 = [(value >> 4) & 1 for value in shared]
        for bus in buses:
            if ([(code >> 3) & 1 for code in mapped_codes(held, bus)] != held_b5 or
                    [(code >> 3) & 1 for code in mapped_codes(shared, bus)] != shared_b5):
                raise ValueError('B5 prediction is not invariant across surviving buses')
        differences = [index for index, (a, b) in enumerate(zip(held_b5, shared_b5))
                       if a != b]
        by_segment = segments(held_b5, shared_b5)
        if sum(by_segment.values()) != len(differences):
            raise ValueError('segment difference count changed')
        cases.append(dict(selector=selector, tx_trace_digest=result['trace_digest'],
                          samples=SAMPLE_COUNT,
                          serial_hold_b5_sha256=hashlib.sha256(bytes(held_b5)).hexdigest(),
                          shared_y_late_clock_b5_sha256=hashlib.sha256(
                              bytes(shared_b5)).hexdigest(),
                          b5_different_samples=len(differences),
                          b5_differences_by_segment=by_segment,
                          first_different_sample_indices=differences[:24],
                          serial_hold_b5_one_count=sum(held_b5),
                          shared_y_b5_one_count=sum(shared_b5),
                          serial_hold_data_errors_by_bus=[x['filtered_data_errors']
                              for x in old['phases'][0]['banks']['256']['bus_scores']],
                          shared_y_data_errors_by_bus=[x['filtered_data_errors']
                              for x in old['phases'][1]['banks']['256']['bus_scores']]))
        print('B5 topology', selector, len(differences), by_segment, flush=True)
    paths = (Path(__file__), PRIOR, BANK, TXREADY, BUSES, PHOTO,
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE / 'joint_mask04_tx_bank_phase.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='visible-candidate DAC08 B5 discriminator for two latch topologies',
                  fixture=dict(serial_hold='74LS373 holds 12A Y before 74LS273 clocks at 127->128',
                               shared_y='74LS273 D sees current Y and clocks after 127 Y settles',
                               b5_route='assumed Y4->74LS273 D4; photo-suggested Q4->DAC08 B5 pin 9',
                               candidate_buses=len(buses),
                               invariant_mapping='Y4->DAC code bit 3 (B5) on all six buses',
                               bank_intervention_mapping='Y0->DAC code bit 4 (B4) on all six buses'),
                  cases=cases,
                  limitations=[
                      'The B5 copper segment is photo-suggested, not continuity-verified; Y4-to-D4 and the latch clocks are untraced.',
                      'This is a digital pin-level prediction from two executed stream interpretations, not a measured DAC08 voltage/current.',
                      'The saved Q=1 filtered data scores are diagnostic and do not identify the physical analog filter.',
                      'The ROM-bank switch alone changes B4, not the visible-candidate B5 segment.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
