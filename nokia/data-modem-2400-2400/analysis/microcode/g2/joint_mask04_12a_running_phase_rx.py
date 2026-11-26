"""Replay 64-count running-phase line through the frozen DSC receiver rule."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_q05_phase_level_map as phase_model
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_offset_visit_phase import project
from zero_run_detector import line_octets
from joint_mask04_q05_fresh_payload_levels import PAYLOADS

HERE = Path(__file__).resolve().parent
TX = HERE / 'results/joint-mask04-12a-running-phase.json'
RULE = HERE / 'results/joint-mask04-q05-phase-level-map.json'


def run(out=HERE / 'results/joint-mask04-12a-running-phase-rx.json'):
    tx = json.loads(TX.read_text())
    rule = json.loads(RULE.read_text())
    phase = {int(key, 16): value for family in ('base_phase', 'learned_phase')
             for key, value in rule['rule'][family].items()}
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for selector, delay in (('40', 5), ('60', 18)):
            row = next(c for c in tx['cases']
                       if c['selector'] == selector and c['offset'] == 64)
            offered = line_octets(PAYLOADS[selector], delay)
            with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
                rx, adc, symbols = loopback.capture(mapping, base, row['pcm'],
                                                    row['expected_dibits'])
            states = alternative_states(project(symbols, 46, 93))
            decoded = phase_model.decode([f'{value:X}' for value in states],
                                         phase)
            readout = line.readout_result(decoded, row['expected_dibits'],
                                          offered, controller, selector, delay)
            result = dict(selector=selector, offset=64,
                          rx_trace_digest=rx['trace_digest'],
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          states=[f'{value:X}' for value in states],
                          unknown_states=sorted({f'{value:X}' for value in states
                                                 if value not in phase}),
                          decoded_dibits=decoded,
                          readout=readout)
            cases.append(result)
            print(selector, 'wrong', len(readout['data_wrong_indices']),
                  'unknown', len(readout['data_unknown_indices']), flush=True)
    report = dict(experiment='running phase perturbation frozen DSC receive',
                  fixture=dict(offset=64, phase_rule='frozen seven-state',
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=['Running R1 intervention and external phase/serial logic are diagnostic hypotheses.',
                               'Physical DAC/ADC/clock/USART routes remain untraced.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), TX, RULE,
                                           HERE / 'joint_mask04_tx_rx_loopback.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
