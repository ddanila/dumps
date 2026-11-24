"""Test counterfactual PROM-bit assignments for the photo-traced I7 route."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'assumed'))
from common import read, save
from execute import execute

MAPPING = HERE / 'results/swapped-sine-loop/phase-20-mapping.json'
SCENARIO = HERE / 'results/swapped-sine-loop/phase-20-scenario.json'
CONSTRAINT = HERE / 'photo-i7-constraint.json'
CYCLES = 512


def run(out):
    constraint = read(CONSTRAINT)
    for name in ('front', 'back'):
        photo = (HERE / constraint[f'{name}_photo']).resolve()
        if hashlib.sha256(photo.read_bytes()).hexdigest() != constraint[f'{name}_sha256']:
            raise ValueError(f'{name} photograph hash mismatch')
    base = read(MAPPING)
    scenario = read(SCENARIO)
    if base['fields']['i']['bits'][7] != '11.6':
        raise ValueError('q3 baseline I7 assignment changed')
    cases = []
    for label, token in [('baseline', '11.6'), ('identity', '11.0'),
                         ('inverted_identity', '!11.0')]:
        mapping = deepcopy(base)
        mapping['name'] = base['name'] + '-photo-i7-' + label
        mapping['fields']['i']['bits'][7] = token
        mapping['fields']['i']['status'] = 'hypothesis'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=path, trace_limit=CYCLES)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
        dispatches = [row for row in trace if row['pc'] == 0x38F]
        outputs = [row for row in trace if 0x392 <= row['pc'] <= 0x39F]
        cases.append(dict(label=label, i7=token, clean=result['clean'],
                          final_pc=f'{result["final_state"]["pc"]:03X}',
                          visited_addresses=len({row['pc'] for row in trace}),
                          input_38e_visits=sum(row['pc'] == 0x38E for row in trace),
                          dispatch_38f_visits=len(dispatches),
                          candidate_output_word_visits=len(outputs),
                          first_output_y=[row['alu']['y'] for row in outputs[:4]],
                          trace_digest=result['trace_digest']))
    sources = [Path(__file__), CONSTRAINT, MAPPING, SCENARIO,
               HERE.parent / 'assumed/execute.py', HERE.parent / 'assumed/common.py',
               HERE.parent / 'model.py']
    report = dict(status='counterfactual-photo-i7-mapping-sensitivity',
                  cycle_limit=CYCLES,
                  hypothesis='U2 I7 appears to come from U6 Q0. PROM-bit assignments are counterfactual: a second photo route suggests U6 D0 shares U11 E4 enable, rather than a PROM data output.',
                  cases=cases,
                  source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sources},
                  limitations=['The photo routes are not continuity measurements.',
                               'The new U6 D0-to-U11 E4 candidate challenges both PROM-bit assignments used here.',
                               'The q3 instruction mapping remains a hypothesis.',
                               'The phase-32 input and ROM gate are diagnostic fixtures.',
                               'Absence of candidate output in this fixture does not exclude the real transmitter.'])
    out.mkdir(parents=True, exist_ok=True)
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    for row in run(HERE / 'results/photo-i7-probe')['cases']:
        print(row['label'], row['i7'], row['input_38e_visits'], row['final_pc'])
