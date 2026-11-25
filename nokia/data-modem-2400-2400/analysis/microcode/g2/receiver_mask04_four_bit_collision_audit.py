"""Separate missing four-bit table entries from irreducible phase collisions."""

import hashlib
import json
from pathlib import Path

from receiver_mask04_four_bit_phase import HERE, PHASE_BY_INPUT
from reference_modem import QUADRANT_TO_DIBIT
from common import save

SOURCE = HERE / 'results/receiver-mask04-four-bit-phase-between.json'


def relative_phases(dibits):
    quadrant = {dibit: index for index, dibit in enumerate(QUADRANT_TO_DIBIT)}
    phases = [0]
    for dibit in dibits[1:]:
        phases.append((phases[-1] + 2 + quadrant[dibit]) & 3)
    return phases


def run(out=HERE / 'results/receiver-mask04-four-bit-collision-audit.json'):
    source = json.loads(SOURCE.read_text())
    expected_dibits = [3] * 32 + source['fixture']['data_dibits']
    phases = relative_phases(expected_dibits)
    rows = []
    for case in source['cases']:
        if len(case['input_codes']) != len(phases):
            raise ValueError('symbol capture length changed')
        groups = {}
        for code, phase in zip(case['input_codes'], phases):
            groups.setdefault(code, set()).add(phase)
        conflicts = {f'{code:04b}': sorted(labels)
                     for code, labels in groups.items() if len(labels) > 1}
        known = [(code, phase) for code, phase in
                 zip(case['input_codes'], phases) if code in PHASE_BY_INPUT]
        mismatches = [sum(PHASE_BY_INPUT[code] != ((phase + offset) & 3)
                          for code, phase in known) for offset in range(4)]
        data_decisions = case['score']['dibits'][32:]
        data_expected = source['fixture']['data_dibits']
        rows.append(dict(degrees=case['degrees'],
                         previously_unseen_codes=case['previously_unseen_codes'],
                         conflicting_codes=conflicts,
                         known_symbols=len(known),
                         known_symbol_mismatches_by_offset=mismatches,
                         minimum_known_symbol_mismatches=min(mismatches),
                         frozen_dibit_errors=case['score']['errors'],
                         frozen_dibit_unknown=case['score']['unknown'],
                         data_dibit_errors=sum(actual is not None and actual != expected
                                               for actual, expected in zip(data_decisions, data_expected)),
                         data_dibit_unknown=sum(actual is None for actual in data_decisions),
                         trace_digest=case['trace_digest']))
    if (len(rows) != 8 or
            not any(row['conflicting_codes'] for row in rows) or
            not all(row['minimum_known_symbol_mismatches'] > 0 for row in rows)):
        raise ValueError('intermediate phase contradiction changed')
    paths = [Path(__file__), SOURCE,
             HERE / 'receiver_mask04_four_bit_phase.py',
             HERE / 'reference_modem.py']
    report = dict(experiment='four-bit receive phase table collision audit',
                  method='Integrate the reference dibits to relative quadrants; test same-code label collisions and all four constant phase offsets against the frozen table.',
                  cases=rows,
                  conclusion='Adding entries for the unseen 0000 and 1000 codes cannot make the frozen four-bit phase table correct at all intermediate angles; four runs have same-code phase collisions, and every run disagrees with at least one already-known code under every constant phase offset.',
                  limitations=['Relative phases come from the known reference stimulus and are not executed DSC output.',
                               'A stateful or multi-visit decoder may still separate the collisions; this only excludes a memoryless table on the four selected bits.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
