"""Screen and run the photo candidate U10 D7 -> U5 Q1 -> U2 A2."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path.insert(0, str(ASSUMED))
from common import read, save
from execute import execute

CATALOG = ASSUMED / 'program-reading.json'
PHOTO_MAPPINGS = HERE / 'results/photo-b-constraints'
BASE_MAPPING = HERE / 'results/swapped-sine-loop/phase-20-mapping.json'
SCENARIO = HERE / 'results/swapped-sine-loop/phase-20-scenario.json'
CONSTRAINT = HERE / 'photo-i7-constraint.json'
CYCLES = 512


def run(out):
    catalog = read(CATALOG)['profiles']
    paths = {name: ASSUMED / path for name, path in catalog.items()}
    paths.update({f'{name}-photo-swapped': PHOTO_MAPPINGS / f'{name}-photo-swapped.json'
                  for name in ('q1', 'q2', 'q3', 'q4')})
    existing = {name: read(path)['fields']['a']['bits'][2] for name, path in paths.items()}
    mapping = read(BASE_MAPPING)
    scenario = read(SCENARIO)
    if mapping['fields']['a']['bits'][2] != '17.7':
        raise ValueError('q3 photo-swap baseline A2 changed')
    cases = []
    for corrected in (False, True):
        for e4, coupled in ((None, False), (1, False), (0, True), (1, True)):
            candidate = deepcopy(mapping)
            fixture = deepcopy(scenario)
            if corrected:
                candidate['name'] += '-photo-a2'
                candidate['fields']['a']['bits'][2] = '10.7'
                candidate['fields']['a']['status'] = 'hypothesis'
                candidate['fields']['a']['evidence'] = (
                    'photo-i7-constraint.json candidate U10 D7 to U5 D1/Q1 to U2 A2')
            if e4 is not None:
                fixture['name'] += f'; candidate E4={e4}'
                fixture['inputs']['instruction_bit_overrides'] = {
                    '7': dict(value=e4, status='hypothesis', evidence=(
                        'photo-i7-constraint.json E4 input to U6 D0/Q0 to U2 I7; '
                        'fixed diagnostic level, latch timing unknown'))}
            if coupled:
                fixture['name'] += '; U2 A0 coupled to I7'
                fixture['inputs']['register_address_bit_overrides'] = {
                    'a': {'0': dict(value=e4, status='hypothesis', evidence=(
                        'photo-i7-constraint.json U6 Q0 candidate route to both U2 I7 and A0'))}}
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                result = execute(candidate, fixture, CYCLES, mode='integrated',
                                 out=path, trace_limit=CYCLES)
                trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
            cases.append(dict(a2=candidate['fields']['a']['bits'][2],
                              i7='PROM-bit baseline' if e4 is None else e4,
                              a0='PROM-bit baseline' if not coupled else e4,
                              clean=result['clean'], final_pc=f'{result["final_state"]["pc"]:03X}',
                              input_38e_visits=sum(row['pc'] == 0x38E for row in trace),
                              candidate_output_word_visits=sum(0x392 <= row['pc'] <= 0x39F for row in trace),
                              visited_addresses=len({row['pc'] for row in trace}),
                              trace_digest=result['trace_digest']))
    sources = [Path(__file__), CATALOG, BASE_MAPPING, SCENARIO, CONSTRAINT,
               HERE.parent / 'assumed/execute.py', HERE.parent / 'assumed/common.py',
               HERE.parent / 'model.py', *paths.values()]
    report = dict(status='photo-a2-candidate-and-bounded-runtime-not-recovered-decode',
                  candidate='U10 pin 17 D7 -> U5 pin 4 D1/Q1 pin 5 -> U2 pin 2 A2',
                  mapped_bit='10.7', existing_a2=existing, cycle_limit=CYCLES,
                  cases=cases,
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources},
                  limitations=['The three visible segments and via registration are photo interpretations, not measured continuity.',
                               'Only A2 is changed; A0/A1/A3 and the rest of the instruction mapping remain hypotheses.',
                               'Fixed E4 levels and I7/A0 coupling are diagnostic assumptions about PROM-enable and latch timing.',
                               'The phase-32 input and ROM gate are diagnostic fixtures; this is not a transmitter demonstration.'])
    out.mkdir(parents=True, exist_ok=True)
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/photo-a2-probe')
    print('Existing A2 source assignments:', report['existing_a2'])
    for case in report['cases']:
        print(case['a2'], case['i7'], case['a0'], case['input_38e_visits'], case['final_pc'])
