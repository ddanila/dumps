"""Screen TEST flag/timing alternatives for sustained high-nibble RAM return."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_ram_pulse_freeze as pulse
import joint_mask04_receive_impulse_memory as impulse
from execute import execute
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit


def run(out=HERE / 'results/joint-mask04-ram-condition-rescue.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    adc = impulse.held_samples(samples, 25, None)
    starts = pulse.sample_starts()
    if samples[25] != 0x51:
        raise ValueError('reference stimulus changed')
    cases = []
    surviving = []
    for timing in ('previous', 'current'):
        for source in ('zero', 'sign', 'carry', 'overflow'):
            for polarity in (0, 1):
                result = execute(mapping, configured(base, adc, timing, source,
                                                     polarity), impulse.CYCLES,
                                 mode='integrated', trace_limit=0)
                visits = result['address_counts'].get(0x3F8, 0)
                cases.append(dict(timing=timing, source=source,
                                  polarity=polarity, feedback=False,
                                  clean=result['clean'], adc_visits=visits,
                                  loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                                  trace_digest=result['trace_digest']))
                if visits == impulse.ADC_VISITS:
                    surviving.append((timing, source, polarity))
    if surviving != [('previous', 'sign', 1), ('previous', 'carry', 1),
                     ('previous', 'overflow', 1)]:
        raise ValueError(('baseline condition survivors changed', surviving))
    instrumented = instrumented_execute()
    for timing, source, polarity in surviving:
        scenario = configured(base, adc, timing, source, polarity)
        scenario.update(external_ram_feedback=True, external_ram_write=True,
                        external_ram_lane='high', external_ram_latch_pc=0x3F9,
                        external_ram_read_pc=0x3FA,
                        external_ram_read_offset=-3,
                        external_ram_write_until=pulse.TRAIN_WRITES,
                        external_ram_address_tick_visits=[4 * visit for visit in starts])
        result = instrumented(mapping, scenario, impulse.CYCLES,
                              mode='integrated', trace_limit=0)
        cases.append(dict(timing=timing, source=source, polarity=polarity,
                          feedback=True, clean=result['clean'],
                          adc_visits=result['address_counts'].get(0x3F8, 0),
                          loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                          first_changed_read=result['external_ram_candidate']['first_changed_read'],
                          trace_digest=result['trace_digest']))
    feedback_counts = {case['source']: case['adc_visits'] for case in cases
                       if case['feedback']}
    if feedback_counts != {'sign': 236, 'carry': impulse.ADC_VISITS,
                           'overflow': 939}:
        raise ValueError(('high-return TEST result changed', feedback_counts))
    report = dict(experiment='condition-source rescue of high-nibble 3FA RAM feedback',
                  fixture=dict(mapping='joint mask04, upper source 17.6',
                               adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                               adc_visits=impulse.ADC_VISITS,
                               cycles=impulse.CYCLES,
                               condition_sources=('zero', 'sign', 'carry', 'overflow'),
                               condition_timing=('previous', 'current'),
                               polarity=(0, 1),
                               feedback='3F9 Y high nibble to sample-paced 256x8 RAM, -3 sample 3FA D high return, D0=1'),
                  cases=cases,
                  limitations=[
                      'TEST-source selection, RAM wiring and D0 forcing are explicit hypotheses.',
                      'Sustaining the four-row loop is a prerequisite, not evidence of echo cancellation.',
                      'The previous-carry result applies to this waveform and must be challenged with own/remote/mixed inputs.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
