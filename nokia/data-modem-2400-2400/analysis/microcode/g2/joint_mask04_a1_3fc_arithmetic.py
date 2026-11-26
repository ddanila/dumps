"""Audit consumed 3FC/3FD operands under the held A1 frame hypothesis."""

import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import joint_mask04_external_ram_echo_screen as echo
import joint_mask04_ram_carry_3fc_arithmetic as arithmetic

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-a1-ram-3fc-echo.json'
MODE01 = HERE / 'results/joint-mask04-ram-carry-3fc-arithmetic.json'


def run(out=HERE / 'results/joint-mask04-a1-3fc-arithmetic.json'):
    saved = json.loads(PRIOR.read_text())
    mode01 = json.loads(MODE01.read_text())
    original = arithmetic.configured

    def a1_configured(*args, **kwargs):
        scenario = original(*args, **kwargs)
        scenario['io']['read']['pc_sequences'][str(0x3EB)] = [0xA1] * (
            4 * echo.VISITS + 1)
        scenario['io']['read']['evidence'] += (
            '; held A1 controller frame byte to D3EB is an assumed route')
        return scenario

    with tempfile.TemporaryDirectory() as temp:
        with patch.object(arithmetic, 'configured', a1_configured):
            raw = arithmetic.run(out=Path(temp) / 'audit.json')
    prior = {(case['stimulus'], case['route']): case
             for case in saved['cases']}
    old = {case['stimulus']: case for case in mode01['cases']}
    summaries = []
    for case in raw['cases']:
        name = case['stimulus']
        before = old[name]
        if (case['trace_digest'] != prior[(name, 'high_return_3fc')][
                'trace_digest'] or
                case['adc_sha256'] != before['adc_sha256'] or
                case['equations_checked'] != {'3fc': echo.TRAIN_VISITS,
                                             '3fd': echo.TRAIN_VISITS}):
            raise ValueError(('A1 full-trace control mismatch', name))
        fields = ('r10_pre3fc', 'carry3fc', 'r5_pre3fd', 'carry3fd')
        new_counts = case['windows']['training']
        old_counts = before['windows']['training']
        summaries.append(dict(stimulus=name,
                              mode01={key: old_counts[key] for key in fields},
                              mode_a1={key: new_counts[key] for key in fields},
                              mode01_y3fd=old_counts['y3fd'],
                              mode_a1_y3fd=new_counts['y3fd']))
    pooled = {key: Counter() for key in
              ('r10_pre3fc', 'carry3fc', 'r5_pre3fd', 'carry3fd')}
    for case in raw['cases']:
        for key in pooled:
            pooled[key].update(case['windows']['training'][key])
    report = dict(experiment='A1-mode 3FC/3FD split-slice operand audit',
                  fixture=dict(mode_3eb='A1 held on 36,001 wrapper visits',
                               ram_return='3F9 Y high -> sample-paced RAM -> 3FC D high, offset -3',
                               trace='all 6,000 training visits at 3FC and 3FD for each of four inputs'),
                  cases=raw['cases'], operand_comparison=summaries,
                  pooled_a1_operands={key: dict(values) for key, values in
                                      pooled.items()},
                  limitations=[
                      'The A1 frame connection, RAM return, TEST and ADC schedule are assumptions.',
                      'Arithmetic operands and Y codes alone do not establish an analog echo residual.',
                      'The mode is held; a real controller train/freeze transition is not yet shown.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR, MODE01,
                                           HERE / 'joint_mask04_ram_carry_3fc_arithmetic.py',
                                           HERE / 'joint_upper_ram_feedback_screen.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['pooled_a1_operands'])
