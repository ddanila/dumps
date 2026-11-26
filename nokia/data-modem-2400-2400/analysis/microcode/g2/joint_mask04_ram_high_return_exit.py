"""Bound a high-nibble 93422 return at the executed 3FA receive word."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_ram_pulse_freeze as pulse
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

ROUTES = (
    ('write_only_3f9', False, True, 0x3F9, False),
    ('read_only', True, False, 0x3F9, False),
    ('feedback_3f9', True, True, 0x3F9, False),
    ('feedback_3fa', True, True, 0x3FA, False),
    ('feedback_3f9_pulse', True, True, 0x3F9, True),
)


def run(out=HERE / 'results/joint-mask04-ram-high-return-exit.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    starts = pulse.sample_starts()
    if samples[25] != 0x51 or starts[25] != 1172:
        raise ValueError('reference input schedule changed')
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, feedback, write, latch_pc, changed in ROUTES:
            adc = impulse.held_samples(samples, 25, 0xB1 if changed else None)
            scenario = configured(base, adc, 'previous', 'overflow', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=write,
                            external_ram_lane='high',
                            external_ram_latch_pc=latch_pc,
                            external_ram_read_pc=0x3FA,
                            external_ram_read_offset=-3,
                            external_ram_write_until=pulse.TRAIN_WRITES,
                            external_ram_address_tick_visits=[4 * visit for visit in starts])
            path = Path(tmp) / name
            result = execute(mapping, scenario, impulse.CYCLES,
                             mode='integrated', out=path,
                             trace_limit=impulse.CYCLES if feedback and write else 0)
            memory = result['external_ram_candidate']
            exits = []
            if feedback and write:
                for line in (path / 'trace.jsonl').open():
                    row = json.loads(line)
                    if row['pc'] == 0x3ED and row['next_pc'] == 0x3EE:
                        exits.append(dict(cycle=row['cycle'],
                                          test=row['test'], q=row['q'],
                                          y=row['alu']['y']))
            cases.append(dict(name=name, latch_pc=f'{latch_pc:03X}',
                              feedback=feedback, write=write, pulse=changed,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              trace_digest=result['trace_digest'],
                              clean=result['clean'],
                              completed_cycles=result['completed_cycles'],
                              adc_visits=result['address_counts'].get(0x3F8, 0),
                              loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                              first_changed_read=memory['first_changed_read'],
                              writes=memory['writes'], reads=memory['reads'],
                              exit_events=exits,
                              final_pc=f"{result['final_state']['pc']:03X}"))
    by_name = {case['name']: case for case in cases}
    controls = (by_name['write_only_3f9'], by_name['read_only'])
    if any(not case['clean'] or case['completed_cycles'] != impulse.CYCLES or
           case['adc_visits'] != impulse.ADC_VISITS or case['loop_exits'] != 0
           for case in controls):
        raise ValueError('high-lane controls did not sustain receive loop')
    for name in ('feedback_3f9', 'feedback_3fa', 'feedback_3f9_pulse'):
        case = by_name[name]
        if (not case['clean'] or case['loop_exits'] != 1 or
                case['adc_visits'] >= starts[25] or len(case['exit_events']) != 1 or
                case['first_changed_read'] is None):
            raise ValueError(('high-lane exit did not reproduce', name))
    if by_name['feedback_3f9']['trace_digest'] != by_name['feedback_3f9_pulse']['trace_digest']:
        raise ValueError('post-exit pulse changed the completed trace')
    report = dict(experiment='high-lane external RAM return at 3FA in real-PROM receive loop',
                  fixture=dict(adc_samples=impulse.SAMPLES,
                               adc_visits=impulse.ADC_VISITS,
                               cycles=impulse.CYCLES,
                               pulse_sample=25, pulse_adc='51 to B1',
                               address='one 3EA tick per held ADC sample',
                               memory='hypothetical 256x8 initially 01, high-nibble Y latch, 3EC writes',
                               return_path='RAM address minus three samples into 3FA D high nibble, D0 forced 1',
                               freeze='writes stop after sample 25'),
                  cases=cases,
                  limitations=[
                      'The high-nibble RAM data, address, write gate and 3FA return are photo-compatible hypotheses, not traced wires.',
                      'The exit rejects these specific routes as sustained receive-loop models; it does not exclude other RAM modes or a separate echo canceller.',
                      'No analog echo residual or received bit is measured.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
