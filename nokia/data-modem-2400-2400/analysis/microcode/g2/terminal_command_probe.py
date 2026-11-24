"""Test an explicit AC=RST pulse at 084 without resetting datapath or stack."""
import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path.insert(0, str(ASSUMED))
from execute import execute
from model import X8X02


def probe():
    base = HERE / 'results/gray-operand-probe/dibit-0'
    mapping = json.loads((base / 'mapping.json').read_text())
    original = json.loads((base / 'scenario.json').read_text())
    original_step = X8X02.step
    cases = []
    for name, values in [('held', [119]), ('changing', [119, 120, 121, 122] * 4)]:
        scenario = copy.deepcopy(original)
        scenario['name'] = 'counterfactual AC=RST at 084, ' + name
        scenario['evidence'] = ('Diagnostic external AC command pulse at terminal 084; '
                                'no override circuit or timing has been traced.')
        scenario['io']['read']['pc_sequences']['790'] = values
        restarts = []

        def step(seq, command, branch=0, test=False):
            if seq.pc == 0x84 and command == 6 and len(restarts) < 15:
                restarts.append(dict(sp=seq.sp, stack=seq.stack[:],
                                     pushes=seq.pushes, pops=seq.pops))
                # The chip's AC=111 operation changes only its next address.
                return original_step(seq, 7, branch, test)
            return original_step(seq, command, branch, test)

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(X8X02, 'step', step):
                result = execute(mapping, scenario, 1900, mode='integrated',
                                 out=directory, trace_limit=1900)
            trace = [json.loads(line) for line in
                     (Path(directory) / 'trace.jsonl').read_text().splitlines()]
        terminal = [row for row in trace if row['pc'] == 0x84]
        reads = [row for row in trace if row['pc'] == 0x317]
        outputs = [row for row in trace if row['pc'] == 0x392]
        if not result['clean'] or len(restarts) != 15 or len(terminal) < 16:
            raise ValueError('restart probe did not complete its bounded fixture')
        if any(row['next_pc'] != 0 for row in terminal[:15]):
            raise ValueError('AC=RST pulse failed to restart at address zero')
        if terminal[15]['next_pc'] != 0x84:
            raise ValueError('terminal self-branch did not resume after pulses')
        if any(event['sp'] != 0 or event['pushes'] != event['pops'] for event in restarts):
            raise ValueError('restart required an unbalanced logical stack')
        expected_y = [10] * 6 if name == 'held' else [10, 34] * 3
        if ([row['alu']['y'] for row in outputs] != expected_y
                or [row['cycle'] for row in outputs] != [55 + 348 * i for i in range(6)]):
            raise ValueError('candidate output pattern changed')
        cases.append(dict(name=name, d316_values=values,
                          restart_cycles=[row['cycle'] for row in terminal[:15]],
                          parked_cycle=terminal[15]['cycle'],
                          restart_stack=restarts,
                          rom_reads=[dict(cycle=row['cycle'],
                                          address=row['external_read']['address'],
                                          value=row['external_read']['value']) for row in reads],
                          candidate_outputs=[dict(cycle=row['cycle'],
                                                  y=row['alu']['y']) for row in outputs],
                          clean=result['clean'], stack=result['stack'],
                          trace_digest=result['trace_digest']))
    paths = [Path(__file__), ASSUMED/'execute.py', ASSUMED/'common.py',
             HERE.parent/'model.py', base/'mapping.json', base/'scenario.json']
    return dict(status='diagnostic hypothesis, not recovered board wiring',
                sequencer_event='replace decoded BRT command at 084 by AC=111 on first 15 arrivals',
                scope='Two continuous q3 runs of 1900 real-PROM instructions; no PC assignment or stack/data reset',
                cases=cases,
                source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in paths})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/terminal-command-probe.json')
    args = parser.parse_args()
    report = probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print([(case['name'], len(case['rom_reads']), case['candidate_outputs'])
           for case in report['cases']])


if __name__ == '__main__':
    main()
