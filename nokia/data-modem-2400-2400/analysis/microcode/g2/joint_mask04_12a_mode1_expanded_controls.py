"""Capture visit 94 on previously passing mode-1 gain controls."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_125gain_holdout as high
import joint_mask04_12a_phasebit0_veto_phase131_holdout as middle
import joint_mask04_12a_row_mode_edge as edge
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OUT = RESULTS / 'joint-mask04-12a-mode1-expanded-controls.json'
VISITS = (46, 47, 93, 94, 141)
CONTROLS = (
    ('1.15', middle,
     RESULTS / 'joint-mask04-12a-phasebit0-veto-phase131-holdout.json'),
    ('1.25', high,
     RESULTS / 'joint-mask04-12a-phasebit0-veto-125gain-holdout.json'),
)


def run(out=OUT):
    cases = []
    with patch.object(edge, 'CAPTURE_VISITS', VISITS):
        for gain, runner, prior in CONTROLS:
            saved = json.loads(prior.read_text())
            expanded = runner.run(out=RESULTS / f'joint-mask04-12a-mode1-expanded-{gain}.json')
            for case, old in zip(expanded['cases'], saved['cases']):
                for key in ('selector', 'payload', 'tx_trace_digest',
                            'rx_trace_digest', 'pc_digest', 'raw_sha256',
                            'pcm_sha256', 'expected_dibits', 'observed_states',
                            'corrected_wrong_indices'):
                    if case[key] != old[key]:
                        raise ValueError(('expanded control changed original run', gain, key))
                for symbol, previous in zip(case['multi_visit_symbols'],
                                            old['multi_visit_symbols']):
                    for visit in ('46', '93'):
                        if symbol['visits'][visit] != previous['visits'][visit]:
                            raise ValueError(('existing capture changed', gain, visit))
                states = [sample_state(symbol, SELECTED)
                          for symbol in case['multi_visit_symbols']]
                cases.append(dict(gain=gain, selector=case['selector'],
                                  rx_trace_digest=case['rx_trace_digest'],
                                  states={f'{state:02X}': sum(x == state for x in states)
                                          for state in sorted(set(states))},
                                  visit94_y_by_state={
                                      f'{state:02X}': sorted({
                                          f"{symbol['visits']['94']['y3f8']:02X}"
                                          for symbol, value in zip(
                                              case['multi_visit_symbols'], states)
                                          if value == state})
                                      for state in sorted(set(states))}))
    paths = (Path(__file__), Path(edge.__file__),
             *(prior for _, _, prior in CONTROLS),
             *(Path(runner.__file__) for _, runner, _ in CONTROLS),
             *(RESULTS / f'joint-mask04-12a-mode1-expanded-{gain}.json'
               for gain, _, _ in CONTROLS))
    report = dict(experiment='visit-94 capture on passing mode-1 gain controls',
                  fixture=dict(gains=['1.15', '1.25'], carrier_offset=131,
                               selectors=['40', '60'], captured_visits=VISITS),
                  cases=cases,
                  limitations=[
                      'Visit 94 is an executed capture point, not a proven board latch edge.',
                      'The DAC/line, ADC, controller mode and serial routes remain assumptions.',
                      'Matching prior traces validates replay, not a new decision circuit.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['gain'], case['selector'],
              {key: case['visit94_y_by_state'].get(key)
               for key in ('1D', '48', '2F')})
