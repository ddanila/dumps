"""Screen one more timed capture after the 0.95x receiver conflict."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_row0_serial_timing as serial
from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import FEATURES, STEPS
from joint_mask04_12a_modebit97_staged_capture import FRESH

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GAIN105 = tuple(RESULTS / f'joint-mask04-12a-modebit100-exact7-gain105-holdout-{mode}-193.json'
                for mode in ('edge32', 'edge48'))
GAIN095 = tuple(RESULTS / f'joint-mask04-12a-modebit101-mixed-gain095-holdout-{mode}-197.json'
                for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit102-gain095-feature-screen.json'
VISITS = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8')


def run(out=OUT):
    cases = []
    paths = []

    def append(path, edge):
        paths.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append(case)

    for path in (*CAPTURES, *RAW):
        append(path, lambda case, path=path: boundary(path, case))
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            append(path, None if mode == 'held81' else
                   48 if mode == 'edge48' else 32)
    for mode, path in zip(('edge32', 'edge48'), FAILED_189):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), FRESH):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), GAIN105):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), GAIN095):
        append(path, 32 if mode == 'edge32' else 48)
    base = solve(cases, FEATURES, STEPS)
    if (len(cases), base['state_codes'], base['directed_conflicts'],
            base['components']) != (108, 102, 218, [102]):
        raise ValueError('joined gain095 conflict graph changed')
    screen = []
    for visit in VISITS:
        for site in SITES:
            for bit in range(8):
                feature = (visit, site, bit)
                if feature in FEATURES:
                    continue
                graph = solve(cases, FEATURES + (feature,), STEPS)
                screen.append(dict(visit=visit, site=site, bit=bit,
                                   state_codes=graph['state_codes'],
                                   directed_conflicts=graph['directed_conflicts'],
                                   components=graph['components']))
    zero = [row for row in screen if row['directed_conflicts'] == 0]
    expected = [(row['visit'], row['site'], row['bit'], row['state_codes'])
                for row in zero]
    if (len(screen), expected) != (76, [('141', 'y3f8', 4, 176),
                                       ('141', 'y3f8', 6, 156)]):
        raise ValueError(('single-bit screen changed', len(screen), expected))
    u3_reclock_changes = {str(bit): sum(
        bool((symbol['visits']['93']['y3f8'] ^
              symbol['visits']['141']['y3f8']) & (1 << bit))
        for case in cases for symbol in case['multi_visit_symbols'])
        for bit in (7, 4, 6)}
    late_cycle = serial.Y3F8_CYCLE + 141 * serial.CYCLES_PER_VISIT
    if late_cycle != 4575 or any(not count for count in u3_reclock_changes.values()):
        raise ValueError('visit-141 timing or U3 recapture control changed')
    sources = (Path(__file__),
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_row0_serial_timing.py', *paths)
    report = dict(experiment='one-bit photo-compatible capture screen after gain095 state conflicts',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               base_features=FEATURES,
                               phase_convention=STEPS,
                               candidate_visits=VISITS,
                               candidate_sites=SITES),
                  base_graph=dict(state_codes=base['state_codes'],
                                  directed_conflicts=base['directed_conflicts'],
                                  components=base['components']),
                  screened_candidates=screen,
                  zero_conflict_candidates=zero,
                  late_capture_cycle=late_cycle,
                  modeled_cycles_to_first_RxC=serial.BIT_CYCLES - late_cycle,
                  U3_second_Y_bits_changed_by_visit141=u3_reclock_changes,
                  limitations=[
                      'A zero-conflict graph is a development consistency test, not a frozen decoder or fresh holdout.',
                      'The visit-141 bit needs a capture or same-cycle consumer; U28 load at cycle 4500 precedes it.',
                      'Reclocking all U3 latches at visit 141 would overwrite its assumed visit-93 second-Y bits in these streams.',
                      'The actual ADC/PROM data path, storage clock and serial nets remain untraced assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('conflicts', result['base_graph']['directed_conflicts'],
          'zero candidates', result['zero_conflict_candidates'])
