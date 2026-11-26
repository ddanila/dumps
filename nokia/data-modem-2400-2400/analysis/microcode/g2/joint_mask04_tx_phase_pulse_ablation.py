"""Check full A4 phase recurrence and causally ablate one controller dibit pulse."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_tx_phase_accumulator as accumulator
from joint_mask04_tx_phase_accumulator import HERE, TXREADY
from photo_joint_tone_training_data import segment2_from_txd
from photo_main_dibit_pulse import (BASE, PULSE_VISITS, VISITS_PER_SYMBOL,
                                    dibit_rule, scenario_inputs)

OUT = HERE / 'results/joint-mask04-tx-phase-pulse-ablation.json'
SYMBOLS = 32
TARGET = 23


def run(out=OUT):
    txready = json.loads(TXREADY.read_text())
    mapping = accumulator.candidate(
        accumulator.mapping_with_upper_source(0, '17.6'),
        accumulator.mapped(accumulator.MAPPINGS['q3']), 4)
    _, base = accumulator.fixture()
    cases = []
    for selector in ('40', '60'):
        controller = next(row for row in txready['cases'] if row['selector'] == selector)
        dibits = segment2_from_txd(controller)
        if len(dibits) != SYMBOLS or dibits[TARGET] != 3:
            raise ValueError(('controller A4 dibits changed', selector))
        ablated = dibits.copy()
        ablated[TARGET] = 0
        normal_inputs = scenario_inputs(dibits)
        control_inputs = scenario_inputs(ablated)
        differing_visits = [index for index, (a, b) in enumerate(
            zip(normal_inputs, control_inputs)) if a != b]
        if differing_visits != list(range(TARGET * VISITS_PER_SYMBOL,
                                          TARGET * VISITS_PER_SYMBOL + PULSE_VISITS)):
            raise ValueError(('ablation changes more than four D127 visits', selector))
        with patch.object(accumulator, 'SYMBOLS', SYMBOLS):
            normal = accumulator.run_case(mapping, base, selector, dibits)
            control = accumulator.run_case(mapping, base, selector, ablated)
        if (normal['cycles'] != control['cycles'] or
                normal['pc127_visits'] != control['pc127_visits'] or
                normal['r1_recurrence_checks'] != control['r1_recurrence_checks'] or
                normal['y7_equals_r1_high_checks'] != control['y7_equals_r1_high_checks'] or
                normal['initial_phase_before_first_input'] !=
                control['initial_phase_before_first_input']):
            raise ValueError(('pulse intervention changed common loop fixture', selector))
        expected_delta = (PULSE_VISITS *
                          (dibit_rule(0, 0) - dibit_rule(1, 1))) & 255
        deltas = [((a['r1'] - b['r1']) & 255) for a, b in
                  zip(control['symbol_ends'], normal['symbol_ends'])]
        if (expected_delta != 128 or deltas !=
                [0] * TARGET + [128] * (SYMBOLS - TARGET) or
                normal['sampled_y7_sha256'] == control['sampled_y7_sha256'] or
                normal['trace_digest'] == control['trace_digest']):
            raise ValueError(('causal phase step changed', selector, deltas))
        cases.append(dict(selector=selector,
                          controller_dibits=dibits,
                          target_symbol_zero_based=TARGET,
                          original_dibit=dibits[TARGET],
                          control_dibit=ablated[TARGET],
                          original_pulse_d127=f'{dibit_rule(1, 1):02X}',
                          control_pulse_d127=f'{BASE:02X}',
                          changed_d127_visits=differing_visits,
                          expected_control_minus_original_phase=expected_delta,
                          symbol_end_phase_delta=deltas,
                          normal=normal, control=control))
        print('full-A4 ablation', selector, 'visits', normal['pc127_visits'],
              'Y7 checks', normal['y7_equals_r1_high_checks'],
              'phase delta', expected_delta, flush=True)
    paths = (Path(__file__), TXREADY,
             HERE / 'joint_mask04_tx_phase_accumulator.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE.parent / 'assumed/execute.py', accumulator.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='full controller A4 R1/Y7 recurrence with one-dibit pulse ablation',
                  fixture=dict(selectors=['40', '60'],
                               data_symbols=SYMBOLS,
                               ablated_symbol_zero_based=TARGET,
                               visits_per_symbol=accumulator.VISITS_PER_SYMBOL,
                               visits_per_sample=accumulator.VISITS_PER_SAMPLE,
                               pulse_visits=PULSE_VISITS,
                               baseline_d127=f'{BASE:02X}'),
                  cases=cases,
                  limitations=[
                      'The controller dibits are real 8031/8251 outputs; D127 pulse decoding and route remain assumed.',
                      'R1 and Y7 are executed internal values; their physical DAC and line connection is untraced.',
                      'The 9,600 Hz latch cadence follows an assumed clock division, not measured hardware.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
