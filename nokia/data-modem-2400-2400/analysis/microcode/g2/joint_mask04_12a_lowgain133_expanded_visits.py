"""Preserve adjacent-visit receive captures on the failed 0.8x fixture."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_lowgain133_challenge as lowgain
import joint_mask04_12a_row_mode_edge as edge
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-lowgain133-expanded-visits.json'
PRIOR = HERE / 'results/joint-mask04-12a-phasebit0-veto-lowgain133-challenge.json'
VISITS = (46, 47, 93, 94, 141)


def run(out=OUT):
    with patch.object(edge, 'CAPTURE_VISITS', VISITS):
        report = lowgain.run(out=out)
    saved = json.loads(PRIOR.read_text())
    occurrences = []
    for case, old in zip(report['cases'], saved['cases']):
        for key in ('selector', 'payload', 'tx_trace_digest',
                    'rx_trace_digest', 'pc_digest', 'raw_sha256',
                    'pcm_sha256', 'expected_dibits', 'observed_states',
                    'corrected_wrong_indices'):
            if case[key] != old[key]:
                raise ValueError(('expanded capture changed original run', key))
        for index, (symbol, previous) in enumerate(zip(
                case['multi_visit_symbols'], old['multi_visit_symbols'])):
            for visit in ('46', '93'):
                if symbol['visits'][visit] != previous['visits'][visit]:
                    raise ValueError(('existing capture changed', visit))
            if sample_state(symbol, SELECTED) == 0x1D:
                occurrences.append(dict(selector=case['selector'],
                                        symbol=index,
                                        visits=symbol['visits']))
    if len(occurrences) != 6:
        raise ValueError(('1D occurrence count changed', len(occurrences)))
    report['experiment'] = 'expanded adjacent-visit capture on phase-133 low-gain failure'
    report['fixture']['captured_visits'] = VISITS
    report['state_1d_occurrences'] = occurrences
    report['limitations'].append(
        'Adjacent visit captures are executed emulator values, not established board latch edges.')
    for path in (Path(__file__), PRIOR, Path(edge.__file__)):
        report['source_sha256'][str(path.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print([(row['selector'], row['symbol'])
           for row in report['state_1d_occurrences']])
