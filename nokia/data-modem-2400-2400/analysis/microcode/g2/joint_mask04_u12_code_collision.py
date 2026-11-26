"""Test a controlled ADC difference that collides at the assumed U12 readout."""

import hashlib
import json
from pathlib import Path

import joint_mask04_receive_impulse_memory as impulse
from joint_mask04_carryover_latch_pulse import capture as latch_capture
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

HERE = Path(__file__).resolve().parent
PULSE_SAMPLE = 25
ADC_CODES = (0x1F, 0x6F)
LATCH_FIELDS = ('qualified_row0', 'live_row3', 'unqualified_before_row3')


def run(out=HERE / 'results/joint-mask04-u12-code-collision.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    captured = []
    for code in ADC_CODES:
        adc = impulse.held_samples([0x7F] * impulse.SAMPLES,
                                   PULSE_SAMPLE, code)
        latch, latch_result = latch_capture(mapping, base, adc)
        state, state_result = impulse.capture(mapping, base, adc)
        if latch_result['trace_digest'] != state_result['trace_digest']:
            raise ValueError('independent captures did not replay the same trace')
        captured.append((latch, state))
        cases.append(dict(pulse_adc=f'{code:02X}',
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          trace_digest=latch_result['trace_digest'],
                          latch_sha256=hashlib.sha256(bytes(
                              row[field] for row in latch for field in LATCH_FIELDS
                          )).hexdigest(),
                          state_sha256=state_result['row_sha256']))
    left_latch, left_state = captured[0]
    right_latch, right_state = captured[1]
    latch_differences = {
        field: [i for i, (a, b) in enumerate(zip(left_latch, right_latch))
                if a[field] != b[field]]
        for field in LATCH_FIELDS
    }
    state_differences = {
        field: [i for i, (a, b) in enumerate(zip(left_state, right_state))
                if a[j] != b[j]]
        for j, field in enumerate(impulse.CHANNELS)
    }
    first_visit = sum(47 if i % 8 < 7 else 46 for i in range(PULSE_SAMPLE))
    last_visit = first_visit + 47
    report = dict(experiment='matched-schedule U12 code collision',
                  fixture=dict(base_adc='7F', pulse_sample=PULSE_SAMPLE,
                               pulse_codes=[f'{code:02X}' for code in ADC_CODES],
                               pulse_visits=[first_visit, last_visit],
                               adc_visits=impulse.ADC_VISITS,
                               cycles_per_replay=impulse.CYCLES),
                  cases=cases,
                  latch_difference_counts={key: len(value) for key, value
                                           in latch_differences.items()},
                  state_difference_counts={key: len(value) for key, value
                                           in state_differences.items()},
                  first_state_difference={key: (value[0] if value else None)
                                          for key, value in state_differences.items()},
                  limitations=[
                      'The two one-sample pulses are synthetic and are not a valid transmitted dibit pair.',
                      'The U12 row-0 clock, input bits, and row-3 consumer are photo-compatible assumptions, not traced connections.',
                      'A collision at this readout does not rule out other DSC outputs or a longer external analog history.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
