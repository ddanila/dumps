"""Compare receive-wrapper decisions under changing and constant ADC streams."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_3eb_adc_route_screen import CYCLES, VISITS, scenario

PCS = (0x3EA, 0x3EB, 0x3EC, 0x3ED)
FIELDS = ('test', 'next_pc', 'q', 'alu.y', 'alu.sign', 'alu.zero',
          'alu.carry', 'alu.overflow')
PATTERNS = ((0, 1, 3, 2), (0, 0, 0, 0))


def capture(mapping, base, pattern):
    samples = codes(pattern, 32, 'complementary')
    visits = [value for index, value in enumerate(samples)
              for _ in range(94 if index % 4 < 3 else 93)]
    if len(visits) != VISITS:
        raise ValueError('ADC hold schedule changed')
    rows = {pc: [] for pc in PCS}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario(base, False, True, visits),
                         CYCLES, mode='integrated', out=temporary,
                         trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if row['pc'] not in rows:
                continue
            rows[row['pc']].append(tuple(
                row['alu'][field[4:]] if field.startswith('alu.')
                else row[field] for field in FIELDS))
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            result['address_counts'].get(0x3F8) != VISITS or
            [len(rows[pc]) for pc in PCS] != [6001, 6001, 6001, 6000]):
        raise ValueError('receive wrapper fixture did not sustain')
    return rows, result['trace_digest'], samples


def run(out=HERE / 'results/receiver-wrapper-decision-probe.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    changing, changing_digest, changing_samples = capture(mapping, base,
                                                           PATTERNS[0])
    constant, constant_digest, constant_samples = capture(mapping, base,
                                                           PATTERNS[1])
    comparison = {}
    for pc in PCS:
        site = {}
        for index, field in enumerate(FIELDS):
            a = [row[index] for row in changing[pc]]
            b = [row[index] for row in constant[pc]]
            differences = [visit for visit, pair in enumerate(zip(a, b))
                           if pair[0] != pair[1]]
            site[field] = dict(changing_unique=len(set(a)),
                               constant_unique=len(set(b)),
                               differing_visits=len(differences),
                               first_difference=(differences[0]
                                                 if differences else None))
        comparison[f'{pc:03X}'] = site
    if (changing_digest == constant_digest or
            any(comparison[f'{pc:03X}'][field]['differing_visits']
                for pc in PCS for field in FIELDS if field != 'q') or
            not all(comparison[f'{pc:03X}']['q']['differing_visits']
                    for pc in PCS)):
        raise ValueError('wrapper contrast changed')
    report = dict(
        experiment='receive-wrapper output comparison, changing versus constant ADC',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario sequence [0,2] at 3EC',
                     adc='complementary 127-PCM at 3F8; 94/94/94/93 visits per sample',
                     cycles=CYCLES, adc_visits=VISITS,
                     fields=list(FIELDS)),
        streams=[dict(pattern=list(pattern),
                      first_adc_codes=[f'{value:02X}' for value in samples[:8]],
                      trace_digest=digest)
                 for pattern, samples, digest in
                 ((PATTERNS[0], changing_samples, changing_digest),
                  (PATTERNS[1], constant_samples, constant_digest))],
        comparison=comparison,
        interpretation=('Wrapper TEST/next-PC and ALU Y/flags do not differ '
                        'between these streams; Q does. This fixture has no '
                        'ADC-dependent decision at the four wrapper words.'),
        limitations=('Only this 32-sample pair, 0/2 dispatch, assumed mapping '
                     'and ADC site are tested; no claim about a physical RxD '
                     'route or other receive routines.'),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for pc, site in result['comparison'].items():
        print(pc, {field: row['differing_visits']
                   for field, row in site.items()})
