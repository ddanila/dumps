"""Diagnose the unseen state in the exact-seven-product holdout."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_0d_feature_graph import code, solve as phase_graph
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import FEATURES, STEPS, gate_phase
from joint_mask04_12a_modebit97_exact_products import solve as product_solve
from joint_mask04_12a_modebit97_staged_capture import FRESH
from joint_mask04_12a_ten_bit_product_bound import cube_hit
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
EXACT = RESULTS / 'joint-mask04-12a-modebit97-exact-products.json'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit100-exact7-gain105-holdout.json'
NEW = tuple(RESULTS / f'joint-mask04-12a-modebit100-exact7-gain105-holdout-{mode}-193.json'
            for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit101-gain105-diagnosis.json'


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
    prior_count = len(cases)
    for mode, path in zip(('edge32', 'edge48'), NEW):
        append(path, 32 if mode == 'edge32' else 48)
    graph = phase_graph(cases, FEATURES, STEPS)
    if (prior_count, len(cases), graph['state_codes'], graph['components'],
            graph['directed_conflicts']) != (100, 104, 101, [101], 0):
        raise ValueError('joined gain105 phase graph changed')
    old_graph = json.loads(EXACT.read_text())['post_holdout_phase_graph']
    new_states = sorted(set(graph['relative_phase']) - set(old_graph['relative_phase']))
    if new_states != ['2DE']:
        raise ValueError(('unseen state population changed', new_states))
    rows = [(int(state, 16), phase) for state, phase in
            graph['relative_phase'].items()]
    bounds = [product_solve(rows, bit, polarity)
              for bit in (0, 1) for polarity in (0, 1)]
    counts = {(row['phase_bit'], row['on_polarity']):
              row['minimum_direct_products'] for row in bounds}
    if counts != {(0, 0): 8, (0, 1): 7, (1, 0): 5, (1, 1): 5}:
        raise ValueError(('post-gain105 product bounds changed', counts))
    exact = json.loads(EXACT.read_text())
    prior_screen = next(screen for screen in exact['screens']
                        if screen['name'] == 'post_holdout_100')
    old_witnesses = [next(row['witness_cubes'] for row in prior_screen['results']
                          if (row['phase_bit'], row['on_polarity']) == (bit, 1))
                     for bit in (0, 1)]
    state = int('2DE', 16)
    witness_phase = sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
                        for bit, terms in enumerate(old_witnesses))
    if (witness_phase, gate_phase(state),
            graph['relative_phase']['2DE']) != (2, 0, 0):
        raise ValueError('unseen-state failure mechanism changed')

    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    holdout_rows = json.loads(HOLDOUT.read_text())['cases']
    replay_rows = []

    def mixed_phase(key):
        return int(any(cube_hit(key, cube) for cube in old_witnesses[0])) | (gate_phase(key) & 2)

    def captured(symbol, variant, covers):
        key = code(symbol, FEATURES)
        return gate_phase(key), serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, key

    def mixed_captured(symbol, variant, covers):
        key = code(symbol, FEATURES)
        return mixed_phase(key), serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, key

    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        for mode, path in zip(('edge32', 'edge48'), NEW):
            for case in json.loads(path.read_text())['cases']:
                selector = case['selector']
                limit = 32 if mode == 'edge32' else 48
                for index, symbol in enumerate(case['multi_visit_symbols']):
                    symbol['visits']['46']['mode_bit5'] = int(index >= limit)
                payload = [int(value, 16) for value in case['payload']]
                offered = line_octets(payload, 5 if selector == '40' else 18)
                with patch.object(serial, 'captured_phase', captured):
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                with patch.object(serial, 'captured_phase', mixed_captured):
                    mixed_score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                prior = next(row for row in holdout_rows
                             if row['mode'] == mode and row['selector'] == selector)
                if (score['wrong_decision_indices'] or
                        not score['recovered_matches_offered'] or
                        score['controller_decoded_bytes'] != payload or
                        score['controller_errors'] or
                        mixed_score['wrong_decision_indices'] or
                        not mixed_score['recovered_matches_offered'] or
                        mixed_score['controller_decoded_bytes'] != payload or
                        mixed_score['controller_errors'] or
                        prior['clipped_samples'] or prior['reference_wrong_indices']):
                    raise ValueError(('old eight-product control changed', mode, selector))
                replay_rows.append(dict(mode=mode, selector=selector,
                                        exact7_wrong_indices=prior['wrong_decision_indices'],
                                        old8_wrong_indices=score['wrong_decision_indices'],
                                        old8_line_exact=score['recovered_matches_offered'],
                                        old8_controller_exact=score['controller_decoded_bytes'] == payload,
                                        posthoc_seven_plus_oldfive_wrong_indices=mixed_score['wrong_decision_indices'],
                                        posthoc_seven_plus_oldfive_controller_exact=mixed_score['controller_decoded_bytes'] == payload,
                                        reference_wrong_indices=prior['reference_wrong_indices'],
                                        clipped_samples=prior['clipped_samples']))

    sources = (Path(__file__), EXACT, HOLDOUT,
               HERE / 'joint_mask04_12a_modebit97_exact_products.py',
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_row0_serial_timing.py', *paths)
    report = dict(experiment='gain105 unseen-state diagnosis and old eight-product controller control',
                  fixture=dict(streams=len(cases), states=graph['state_codes'],
                               new_states=new_states,
                               controller_probe_sha256=controller_sha),
                  joined_phase_graph=graph,
                  post_gain105_direct_product_bounds=bounds,
                  exact_seven_five_phase_at_2DE=witness_phase,
                  observed_phase_at_2DE=graph['relative_phase']['2DE'],
                  old8_phase_at_2DE=gate_phase(state),
                  holdout_replays=replay_rows,
                  limitations=[
                      'The frozen seven/five witness was fixed before offset-193 and fails state 2DE through phase bit 1, not phase bit 0.',
                      'Combining its seven-product bit 0 with the older five-product bit 1 is a post-hoc repair on these streams, not a fresh holdout.',
                      'The older eight-product Boolean gate passes under the same assumed line, mode, capture and USART wiring; its photographed-package realization remains unknown.',
                      'The seven-product lower/upper bound is direct SOP on 101 observed labels only; it does not establish robustness on unobserved states or a multistage circuit.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('states', result['fixture']['states'],
          'old8 pass', sum(row['old8_controller_exact'] for row in result['holdout_replays']),
          'of', len(result['holdout_replays']))
