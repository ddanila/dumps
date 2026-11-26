"""Audit matched original/low-gain phase-133 PROM and serial results."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
CONTROL = RESULTS / 'joint-mask04-12a-phasebit0-veto-baseline133-control.json'
LOW = RESULTS / 'joint-mask04-12a-phasebit0-veto-lowgain133-challenge.json'
LOW_AUDIT = RESULTS / 'joint-mask04-12a-phasebit0-veto-lowgain133-audit.json'
OUT = RESULTS / 'joint-mask04-12a-phasebit0-veto-lowgain133-matched-audit.json'


def run(out=OUT):
    control = json.loads(CONTROL.read_text())
    low = json.loads(LOW.read_text())
    audit = json.loads(LOW_AUDIT.read_text())
    if (control['fixture']['R1_offset'] != 133 or
            low['fixture']['R1_offset'] != 133 or
            control['fixture']['gain_factor'] != 1.0 or
            low['fixture']['gain_factor'] != 0.8 or
            audit['inferred_1d_phase'] != 0):
        raise ValueError('matched low-gain fixtures changed')
    cases = []
    for original, attenuated in zip(control['cases'], low['cases']):
        before = {sample_state(symbol, SELECTED) for symbol in
                  original['multi_visit_symbols']}
        after = {sample_state(symbol, SELECTED) for symbol in
                 attenuated['multi_visit_symbols']}
        payload = [int(value, 16) for value in original['payload']]
        clean = original['corrected_serial']
        wrong = attenuated['corrected_serial']
        if (original['selector'] != attenuated['selector'] or
                original['payload'] != attenuated['payload'] or
                original['tx_trace_digest'] != attenuated['tx_trace_digest'] or
                original['raw_sha256'] != attenuated['raw_sha256'] or
                original['pcm_sha256'] == attenuated['pcm_sha256'] or
                original['pc_digest'] != attenuated['pc_digest'] or
                0x1D in before or 0x1D not in after or
                original['corrected_wrong_indices'] or
                not attenuated['corrected_wrong_indices'] or
                not clean['recovered_matches_offered'] or
                clean['controller_decoded_bytes'] != payload or
                wrong['recovered_matches_offered'] or
                wrong['controller_decoded_bytes'] == payload or
                original['clipped_samples'] or attenuated['clipped_samples']):
            raise ValueError(('matched low-gain audit failed',
                              original['selector']))
        cases.append(dict(selector=original['selector'],
                          same_payload_tx_raw_and_pc=True,
                          changed_pcm_and_rx_trace=True,
                          control_states=sorted(f'{value:02X}' for value in before),
                          attenuated_states=sorted(f'{value:02X}' for value in after),
                          control_veto_errors=0,
                          attenuated_veto_errors=len(
                              attenuated['corrected_wrong_indices']),
                          control_exact_controller_bytes=True,
                          attenuated_exact_controller_bytes=False,
                          clipping_at_either_gain=False))
    if (len(cases) != 2 or
            [case['attenuated_veto_errors'] for case in cases] != [4, 7]):
        raise ValueError('matched low-gain coverage changed')
    paths = (Path(__file__), CONTROL, LOW, LOW_AUDIT)
    report = dict(experiment='matched phase-133 calibrated versus 0.8x gain audit',
                  cases=cases,
                  limitations=[
                      'The gain is a modeled receive-line scaling, not a measured modem adjustment.',
                      'The matched control attributes the capture-family and candidate-readout change to the gain setting under the stated assumed circuit; it does not identify the physical ADC or logic nets.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(run()['cases'])
