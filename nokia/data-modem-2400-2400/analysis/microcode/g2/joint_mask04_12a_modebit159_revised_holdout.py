"""Fresh higher-level challenge of the 159-state thirteen-bit phase witness."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_modebit156_gain100_holdout as prior
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
BASE = RESULTS / 'joint-mask04-12a-modebit156-exact-products.json'
DIAGNOSIS = RESULTS / 'joint-mask04-12a-modebit159-nominal-diagnosis.json'
CANDIDATE = RESULTS / 'joint-mask04-12a-modebit159-revised-cover.json'
GAIN = RESULTS / 'joint-mask04-12a-modebit159-gain115-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-modebit159-gain115-holdout.json'
OFFSET = 201
FACTOR = 1.15
PAYLOADS = {
    '40': (0xA2, 0x6D, 0x13, 0xC5, 0x08, 0xF4, 0x7B, 0x90),
    '60': (0x4E, 0xB8, 0x21, 0xD7, 0x65, 0x0A, 0xF3, 0x9C),
}


def make_candidate():
    candidate = json.loads(BASE.read_text())
    diagnosis = json.loads(DIAGNOSIS.read_text())
    bounds = diagnosis['direct_product_bounds']
    cubes = [next(row['witness_cubes'] for row in bounds
                  if (row['phase_bit'], row['on_polarity']) == (bit, 1))
             for bit in (0, 1)]
    rows = [(int(state, 16), phase) for state, phase in
            diagnosis['joined_phase_graph']['relative_phase'].items()]
    if (len(rows), len(cubes[0]), len(cubes[1])) != (159, 8, 5):
        raise ValueError('revised thirteen-bit candidate changed')
    if any(sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
               for bit, terms in enumerate(cubes)) != phase
           for state, phase in rows):
        raise ValueError('revised witness differs from 159-state graph')
    candidate['bounds'] = bounds
    candidate['candidate'] = dict(
        name='post-offset199 exact eight/five-product witness',
        fitted_observed_states=159,
        selected_after='offset-199 nominal edge-48 call mislabel at 190C',
        warning='Offset 199 is development evidence for this witness; offset 201 is untouched.')
    candidate['candidate_sources'] = {
        str(path.relative_to(HERE.parents[4])):
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (BASE, DIAGNOSIS, Path(__file__))}
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
        row['unseen_vs_159_states'] = sorted(
            key for key in row['unseen_keys'] if f'{int(key, 16):03X}' not in known)
    report['experiment'] = 'fresh offset-201 1.15x challenge of post-159-state thirteen-bit cover'
    report['fixture']['fitted_observed_states'] = 159
    report['fixture']['candidate_cover'] = CANDIDATE.name
    report['limitations'].append(
        'The phase-bit-1 witness was revised after offset-199; only offset-201 is untouched validation.')
    for path in (Path(__file__), CANDIDATE, DIAGNOSIS):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    for mode in ('edge32', 'edge48'):
        prior_path = RESULTS / f'joint-mask04-12a-modebit156-gain100-holdout-{mode}-{OFFSET}.json'
        path = RESULTS / f'joint-mask04-12a-modebit159-gain115-holdout-{mode}-{OFFSET}.json'
        raw = json.loads(prior_path.read_text())
        raw['experiment'] = 'fresh 1.15x real-PROM revised thirteen-bit mode-boundary challenge'
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
