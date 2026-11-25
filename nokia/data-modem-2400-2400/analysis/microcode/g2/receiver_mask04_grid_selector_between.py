"""Challenge the frozen grid selector on saved intermediate-angle PROM runs."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_grid_preamble_selector import analyze

GRID = HERE / 'results/receiver-mask04-grid-preamble-selector.json'
CAPTURES = HERE / 'results/receiver-mask04-multivisit-capture.json'


def run(out=HERE / 'results/receiver-mask04-grid-selector-between.json'):
    grid = json.loads(GRID.read_text())
    if grid['aggregate'] != dict(checks=128, errors=0, unknown=0,
                                  unselected=0, preamble_checks=248,
                                  preamble_errors=0, preamble_unknown=0):
        raise ValueError('frozen grid result changed')
    source = json.loads(CAPTURES.read_text())
    cases = [analyze(case) for case in source['cases']]
    summary = dict(cases=len(cases),
                   unselected=sum(row['selected_data'] is None for row in cases),
                   selected_complete_correct=sum(
                       row['selected_data'] is not None and
                       row['selected_data']['errors'] == 0 and
                       row['selected_data']['unknown'] == 0 for row in cases))
    paths = [Path(__file__), GRID, CAPTURES,
             HERE / 'receiver_mask04_grid_preamble_selector.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py']
    report = dict(experiment='frozen grid preamble selector on intermediate-angle executed captures',
                  fixture=dict(angles=source['fixture']['degrees'],
                               source_seed=source['fixture']['seed'],
                               selector_visit=94, decoder_visit=47),
                  cases=cases, summary=summary,
                  limitations=[
                      'These saved intermediate-angle traces are not a fresh independent stream; they were not used to fit the grid selector.',
                      'The readout, latches, symbol clock and USART path remain external hypotheses.',
                      'Failure of this fixed selector does not rule out an executed phase tracker or other multi-visit consumer.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summary'])
