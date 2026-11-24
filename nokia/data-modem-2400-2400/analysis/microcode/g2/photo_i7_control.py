"""Run q3 with the candidate latched E4-side I7 line at fixed diagnostic levels."""
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
    mapping = read(MAPPING)
    baseline = read(SCENARIO)
    cases = []
    for level in (None, 0, 1):
        scenario = deepcopy(baseline)
        if level is not None:
            scenario['name'] += f'; candidate E4-to-I7 constant {level}'
            scenario['inputs']['instruction_bit_overrides'] = {
                '7': dict(value=level, status='hypothesis', evidence=(
                    'photo-i7-constraint.json candidate U11 E4 input to U6 D0, '
                    'then U6 Q0 to U2 I7; fixed diagnostic level, driver and latch timing unknown.'))}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=path, trace_limit=CYCLES)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
        effective = [row['instruction_i'] for row in trace] if level is not None else []
        if effective and any((value >> 7) & 1 != level for value in effective):
            raise ValueError('instruction bit override did not reach every executed word')
        cases.append(dict(level='PROM-bit baseline' if level is None else level,
                          clean=result['clean'], final_pc=f'{result["final_state"]["pc"]:03X}',
                          visited_addresses=len({row['pc'] for row in trace}),
                          input_38e_visits=sum(row['pc'] == 0x38E for row in trace),
                          candidate_output_word_visits=sum(0x392 <= row['pc'] <= 0x39F for row in trace),
                          trace_digest=result['trace_digest'],
                          first_64_pcs=[f'{row["pc"]:03X}' for row in trace[:64]]))
    sources = [Path(__file__), MAPPING, SCENARIO, CONSTRAINT,
               HERE.parent / 'assumed/execute.py', HERE.parent / 'assumed/common.py',
               HERE.parent / 'model.py']
    report = dict(status='photo-candidate-fixed-control-levels-not-recovered-wiring',
                  cycle_limit=CYCLES, cases=cases,
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources},
                  limitations=['E4-side signal driver, polarity and U6 latch timing are untraced.',
                               'Constant levels are diagnostic alternatives, not established board behavior.',
                               'The q3 mapping, ROM gate and phase-32 startup fixture are hypotheses.',
                               'No candidate output in this fixture is not proof that the modem cannot transmit.'])
    out.mkdir(parents=True, exist_ok=True)
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    for case in run(HERE / 'results/photo-i7-control')['cases']:
        print(case['level'], case['clean'], case['input_38e_visits'], case['final_pc'])
