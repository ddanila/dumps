"""Check the stationary data-mode carrier at the 12A DAC candidate."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END
from photo_joint_tone_training_data import SEGMENT_SYMBOLS
from reference_modem import spectral_peak
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
DEMO = RESULTS / 'joint-mask04-end-to-end-demo.json'
BUSES = line.BUSES
OUT = RESULTS / 'joint-mask04-stationary-carrier-control.json'


def run(out=OUT):
    demo = json.loads(DEMO.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    payload = [int(value, 16) for value in demo['fixture']['payload']]
    offered = line_octets(payload, 5)
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    original = line.buffered_inputs

    def stationary_inputs(values):
        inputs, dibits, events = original(values)
        prefix = SEGMENT_SYMBOLS * line.VISITS_PER_SYMBOL
        changed = inputs[:prefix] + [line.BASE] * (len(inputs) - prefix)
        if len(changed) != len(inputs) or line.BASE != 0xB0:
            raise ValueError('stationary D127 input fixture changed')
        return changed, dibits, events

    with patch.object(line, 'buffered_inputs', stationary_inputs):
        tx, raw, _ = line.transmitter(
            capturing_execute((frozen.PHASE_VISIT, 203)),
            mapping, base, offered)
    if (len(raw) != demo['chain']['tx_12a_samples'] or
            tx['trace_digest'] == demo['chain']['tx_prom_trace_sha256']):
        raise ValueError('stationary intervention did not change the transmit run')
    data_start = SILENCE_END + SEGMENT_SYMBOLS * 8
    rows = []
    for index, bus in enumerate(buses):
        codes = mapped_codes(raw, bus)
        tone = spectral_peak([value - 128 for value in codes[64:TONE_END]],
                             lower=100, upper=3500)
        data = spectral_peak([value - 128 for value in codes[
            data_start:data_start + SEGMENT_SYMBOLS * 8]],
            lower=100, upper=3500)
        rows.append(dict(bus_index=index, mapping=bus,
                         tone_peak_hz=tone['frequency_hz'],
                         stationary_data_peak_hz=data['frequency_hz'],
                         dac_code_sha256=hashlib.sha256(bytes(codes)).hexdigest()))
    if any(row['tone_peak_hz'] != 2100 or
           row['stationary_data_peak_hz'] != 1800 for row in rows):
        raise ValueError('stationary carrier spectrum differs from expectation')
    paths = (Path(__file__), DEMO, BUSES,
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='stationary 1800 Hz data-mode control for 12A DAC candidate',
                  fixture=dict(selector='40', carrier_offset=203,
                               data_mode_D127='B0 held after segment 1',
                               stationarity='counterfactual input control; not real 8031 TxD payload',
                               candidate_sample_rate_hz=9600,
                               sample_count=len(raw), data_window_samples=SEGMENT_SYMBOLS * 8),
                  tx_prom_trace_sha256=tx['trace_digest'], cases=rows,
                  limitations=[
                      'The B0 hold is a controlled stationary input, not the real controller scrambled data stream.',
                      'The output bytes are assumed settled 12A Y mapped to candidate DAC08 pins; physical line and clock remain untraced.',
                      'An FFT peak on a stationary control does not establish the spectrum of every modulated payload or the physical analog line.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('stationary data peaks', [row['stationary_data_peak_hz'] for row in rows])
    return report


if __name__ == '__main__':
    run()
