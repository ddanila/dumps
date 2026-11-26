"""Replace each selected Am27S31 bank in the controller-fed PROM transmitter."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_four_row_retention_tx as joint


def run(out=HERE / 'results/joint-mask04-tx-rom-bank-ablation.json'):
    controller = json.loads(joint.TXREADY.read_text())
    prior = json.loads((HERE / 'results/joint-four-row-retention-tx.json').read_text())
    buses = json.loads(joint.BUSES.read_text())['zero_error_survivors']
    mapping = joint.candidate(joint.mapping_with_upper_source(0, '17.6'),
                              joint.mapped(joint.MAPPINGS['q3']), 4)
    _, base = joint.fixture()
    original_execute = joint.execute

    cases = []
    for selector in ('40', '60'):
        tx_case = next(row for row in controller['cases']
                       if row['selector'] == selector)
        baseline = next(row for row in prior['transmit_mask04']
                        if row['selector'] == selector)
        row = dict(selector=selector,
                   baseline=dict(trace_digest=baseline['trace_digest'],
                                 sample_sha256=baseline['raw_y_sample_sha256'],
                                 candidate_waveform=baseline['complete_candidate_waveform'],
                                 bus_scores=[dict(bus_index=item['bus_index'],
                                                  peak_hz=item['late_a1_peak_hz'],
                                                  data_errors=item['filtered_data_errors'])
                                             for item in baseline['bus_cases']]))
        for pc in (0x129, 0x12E):
            visits = {}

            def lower_one_bank(mapping, scenario, cycles, **kwargs):
                assert scenario['io']['read']['address']['bank_by_pc'] == {
                    str(0x129): 256, str(0x12E): 256}
                scenario['io']['read']['address']['bank_by_pc'][str(pc)] = 0
                scenario['name'] += f'; counterfactual lower ROM bank at PC{pc:03X}'
                result = original_execute(mapping, scenario, cycles, **kwargs)
                visits['target_pc'] = result['address_counts'].get(pc, 0)
                return result

            with patch.object(joint, 'execute', lower_one_bank):
                counterfactual = joint.transmit_case(mapping, base, tx_case, buses)
            row[f'lower_pc{pc:03x}'] = counterfactual
            row[f'pc{pc:03x}_visits'] = visits['target_pc']
            row[f'pc{pc:03x}_trace_changed'] = (
                counterfactual['trace_digest'] != baseline['trace_digest'])
            print(selector, f'{pc:03X}',
                  counterfactual['complete_candidate_waveform'],
                  counterfactual.get('pc129_visits'),
                  [(item['late_a1_peak_hz'], item['filtered_data_errors'])
                   for item in counterfactual.get('bus_cases', [])], flush=True)
        cases.append(row)
    paths = (Path(__file__), joint.TXREADY,
             HERE / 'results/joint-four-row-retention-tx.json', joint.BUSES,
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE.parent / 'assumed/execute.py', joint.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='controller-fed mask04 transmitter selected-ROM-bank ablations',
                  intervention='Separately change Am27S31 A8 at PC129 or PC12E from upper to lower bank; retain the other upper-bank read, controller input, mapping, clock, latch and bus hypotheses.',
                  cases=cases,
                  limitations=['A ROM-bank intervention tests modeled causal dependence, not the physical A8 wire.',
                               'DAC latch, bus, analog filter and line output remain candidate routes.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
