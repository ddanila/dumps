"""Fresh real-PROM challenge of the post-gain105 seven/old-five phase cover."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_modebit100_exact7_holdout as prior
from joint_mask04_12a_modebit97_cover import P1_CUBES
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
EXACT = RESULTS / 'joint-mask04-12a-modebit97-exact-products.json'
DIAGNOSIS = RESULTS / 'joint-mask04-12a-modebit101-gain105-diagnosis.json'
CANDIDATE = RESULTS / 'joint-mask04-12a-modebit101-mixed-cover.json'
GAIN = RESULTS / 'joint-mask04-12a-modebit101-mixed-gain095-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-modebit101-mixed-gain095-holdout.json'
OFFSET = 197
FACTOR = 0.95
PAYLOADS = {
    '40': (0x34, 0xB1, 0x7A, 0xE6, 0x0D, 0xC8, 0x52, 0x9F),
    '60': (0x8A, 0x45, 0xD2, 0x1C, 0xF7, 0x60, 0x3B, 0xAE),
}


def make_candidate():
    candidate = json.loads(EXACT.read_text())
    diagnosis = json.loads(DIAGNOSIS.read_text())
    screen = next(row for row in candidate['screens']
                  if row['name'] == 'post_holdout_100')
    bit0 = next(row['witness_cubes'] for row in screen['results']
                if (row['phase_bit'], row['on_polarity']) == (0, 1))
    bit1 = next(row for row in screen['results']
                if (row['phase_bit'], row['on_polarity']) == (1, 1))
    bit1['witness_cubes'] = list(P1_CUBES)
    rows = [(int(state, 16), phase) for state, phase in
            diagnosis['joined_phase_graph']['relative_phase'].items()]
    if (len(rows), len(bit0), len(bit1['witness_cubes'])) != (101, 7, 5):
        raise ValueError('mixed-cover source population changed')
    if any((int(any(cube_hit(state, cube) for cube in bit0)) |
            (int(any(cube_hit(state, cube) for cube in bit1['witness_cubes'])) << 1))
           != phase for state, phase in rows):
        raise ValueError('mixed cover does not fit the 101-state diagnosis')
    candidate['candidate'] = dict(
        name='seven-product bit 0 plus older five-product bit 1',
        selected_after='offset-193 gain-1.05 diagnosis of phase-bit-1 error at 2DE',
        fitted_observed_states=101,
        warning='This is a refit, not the offset-193 holdout witness.')
    candidate['candidate_sources'] = {
        str(path.relative_to(HERE.parents[4])):
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (EXACT, DIAGNOSIS,
                     HERE / 'joint_mask04_12a_modebit97_cover.py', Path(__file__))}
    CANDIDATE.write_text(json.dumps(candidate, indent=2) + '\n')


def run(out=OUT):
    make_candidate()
    with patch.object(prior, 'EXACT', CANDIDATE), \
            patch.object(prior, 'GAIN', GAIN), \
            patch.object(prior, 'OFFSET', OFFSET), \
            patch.object(prior, 'FACTOR', FACTOR), \
            patch.object(prior, 'PAYLOADS', PAYLOADS):
        report = prior.run(out=out, capture=True)
    known = set(json.loads(DIAGNOSIS.read_text())['joined_phase_graph']['relative_phase'])
    for row in report['cases']:
        row['unseen_vs_101_states'] = sorted(set(row['unseen_keys']) - known)
    report['experiment'] = 'fresh offset-197 0.95x challenge of post-gain105 mixed seven/five-product cover'
    report['fixture']['fitted_observed_states'] = 101
    report['fixture']['candidate_cover'] = CANDIDATE.name
    report['limitations'].append(
        'The mixed cover was chosen after offset-193 exposed a phase-bit-1 failure; only offset-197 is untouched validation.')
    for path in (Path(__file__), CANDIDATE, DIAGNOSIS):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    for mode in ('edge32', 'edge48'):
        prior_path = RESULTS / f'joint-mask04-12a-modebit100-exact7-gain105-holdout-{mode}-{OFFSET}.json'
        path = RESULTS / f'joint-mask04-12a-modebit101-mixed-gain095-holdout-{mode}-{OFFSET}.json'
        raw = json.loads(prior_path.read_text())
        raw['experiment'] = 'fresh 0.95x real-PROM mixed seven/five-product mode-boundary challenge'
        raw['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        raw['source_sha256'][str(CANDIDATE.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(CANDIDATE.read_bytes()).hexdigest())
        path.write_text(json.dumps(raw, indent=2) + '\n')
        prior_path.unlink()
        del report['source_sha256'][str(prior_path.relative_to(HERE.parents[4]))]
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
