"""Retest G1 quarter-turn tables under photo-constrained coupled pin routes."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import decode, read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from rotation_study import put, run_entry, scenario_for, word

CONFIG = ASSUMED / 'rotation-search.json'
BASELINE = ASSUMED / 'results/independent-study/variant-3.json'
TABLES = (0x3C5, 0x3DA)
PAIRS = ((0x1234, 0x5678), (1, 0), (0, 1))


def quarter_turns(x, y):
    return ((x, y), ((-y) & 65535, x), ((-x) & 65535, (-y) & 65535),
            (y, (-x) & 65535))


def sign_selections(x, y):
    return ((x, y), (x, (-y) & 65535),
            ((-x) & 65535, (-y) & 65535), ((-x) & 65535, y))


def local_output(rows, policy, table, entry, x, y, source_bases, output_base,
                 i0=None, e4_pattern=None, uncoupled_a_pattern=None):
    candidate = list(rows)
    for position in range(4):
        pc = table + 4*entry + position
        row = dict(candidate[pc])
        if e4_pattern is not None:
            e4 = (e4_pattern >> position) & 1
            row['i'] = (row['i'] & ~129) | i0 | (e4 << 7)
            row['a'] = (row['a'] & ~3) | e4  # A0=I7=E4, A1=E2=0
        elif uncoupled_a_pattern is not None:
            a0 = (uncoupled_a_pattern >> position) & 1
            row['i'] = (row['i'] & ~129) | 128  # I7=1, I0=0
            row['a'] = (row['a'] & ~3) | a0
        candidate[pc] = row
    ram = [0xA5]*16
    put(ram, source_bases[0], x)
    put(ram, source_bases[1], y)
    cpu, trace = run_entry(candidate, table, entry, ram, 0, policy)
    return (word(cpu.ram, output_base), word(cpu.ram, output_base+2)), trace


def run(out):
    config = read(CONFIG)
    original = read(BASELINE)
    baseline_rows = decode(original)
    baseline_policy = scenario_for(original, config)['inputs']['carry']
    baseline_matched = 0
    for table, dest in ((0x3C5, 4), (0x3DA, 8)):
        for x, y in PAIRS:
            for entry, expected in enumerate(quarter_turns(x, y)):
                got, _ = local_output(baseline_rows, baseline_policy, table,
                                      entry, x, y, (10, 12), dest)
                baseline_matched += got == expected
    if baseline_matched != 24:
        raise ValueError('original G1 local quarter-turn baseline changed')

    cases = []
    for name, path in MAPPINGS.items():
        mapping = mapped(path)
        rows = decode(mapping)
        policy = scenario_for(mapping, config)['inputs']['carry']
        destinations = sorted({
            (((rows[pc]['i'] & ~129) >> 6) & 7,
             (((rows[pc]['i'] & ~129) | 128) >> 6) & 7)
            for table in TABLES for pc in range(table, table+16)})
        if destinations != [(1, 3)]:
            raise ValueError(f'{name}: I7 no-load/write relation changed')

        coupled = []
        coupled_witness = []
        for i0 in (0, 1):
            for pattern in range(16):
                matched = 0
                for table in TABLES:
                    for x, y in PAIRS:
                        for entry, expected in enumerate(quarter_turns(x, y)):
                            got, _ = local_output(rows, policy, table, entry,
                                                  x, y, (4, 8), 10,
                                                  i0=i0, e4_pattern=pattern)
                            matched += got == expected
                            if (name == 'q3' and i0 == 0 and pattern == 15
                                    and table == 0x3C5 and (x, y) == PAIRS[0]):
                                coupled_witness.append(dict(entry=entry, got=list(got),
                                                            quarter_turn=list(expected)))
                coupled.append(dict(i0=i0,
                                    e4_pattern=''.join(str((pattern >> pos) & 1)
                                                       for pos in range(4)),
                                    quarter_turn_matches=matched, checks=24))
        if any(item['quarter_turn_matches'] for item in coupled):
            raise ValueError(f'{name}: coupled table unexpectedly rotates')

        # Separate A0 from I7 to show what the photo A/B reassignment alone does.
        sign_matches = rotation_matches = 0
        witness = []
        for table in TABLES:
            for x, y in PAIRS:
                for entry in range(4):
                    got, _ = local_output(rows, policy, table, entry,
                                          x, y, (4, 8), 10,
                                          uncoupled_a_pattern=0b1010)
                    sign_matches += got == sign_selections(x, y)[entry]
                    rotation_matches += got == quarter_turns(x, y)[entry]
                    if name == 'q3' and table == 0x3C5 and (x, y) == PAIRS[0]:
                        witness.append(dict(entry=entry, got=list(got),
                                            quarter_turn=list(quarter_turns(x, y)[entry])))
        if sign_matches != 24 or rotation_matches != 12:
            raise ValueError(f'{name}: uncoupled sign-selection control changed')
        cases.append(dict(mapping=name,
                          table_bases=[f'{table:03X}' for table in TABLES],
                          e4_coupled_destination_codes=dict(low=1, high=3),
                          coupled_patterns=coupled,
                          coupled_best_quarter_turn_matches=0,
                          coupled_all_high_witness=coupled_witness,
                          uncoupled_control=dict(a0_pattern='0101 in word order',
                                                 i7=1, i0=0, source_register_bases=[4, 8],
                                                 destination_register_bases=[10, 12],
                                                 sign_selection_matches=sign_matches,
                                                 quarter_turn_matches=rotation_matches,
                                                 checks=24, witness=witness)))
    paths = [Path(__file__), CONFIG, BASELINE, HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py', HERE/'photo-b-constraints.json',
             HERE/'photo-a-input-constraint.json', HERE/'photo-i7-constraint.json',
             ASSUMED/'rotation_study.py', ASSUMED/'execute.py',
             HERE.parent/'model.py', *MAPPINGS.values()]
    report = dict(status='photo-constrained local transform test, not recovered board decode',
                  baseline=dict(mapping='q3 original G1 mapping',
                                source_register_bases=[10, 12],
                                destination_register_bases_by_table=[4, 8],
                                quarter_turn_matches=baseline_matched, checks=24),
                  fixture=dict(source_pairs=[list(pair) for pair in PAIRS],
                               carry_policy='G1 mapped-or-previous', q=0, d=0x96,
                               e2_read_level=0,
                               e4_coupled_to_both_u2_i7_and_a0=True,
                               input_sources='A2/A3 and B field from photo hypotheses'),
                  cases=cases,
                  limitations=[
                      'The photo pin routes have pad/via gaps and are candidates, not continuity measurements.',
                      'Each table entry is executed locally for four real-PROM words; no controller call, DAC output or ADC path participates.',
                      'The coupled E4 patterns generously allow held PROM bytes when E4 is low; the actual latch phase is unknown.',
                      'The original quarter-turn identities were search constraints; this comparison cannot by itself identify the modem algorithm.',
                      'The local Am2901 model still shares instruction controls across both slices; separate-slice instructions could change the result.',
                      'The uncoupled control deliberately breaks the photo-candidate A0/I7 tie to isolate register addressing.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-transform-check.json')
    print('baseline', report['baseline']['quarter_turn_matches'])
    print([(row['mapping'], row['coupled_best_quarter_turn_matches'],
            row['uncoupled_control']['sign_selection_matches'])
           for row in report['cases']])
