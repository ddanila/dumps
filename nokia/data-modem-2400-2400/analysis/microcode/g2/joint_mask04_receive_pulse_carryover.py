"""Find every executed difference after one ADC pulse and before/after rejoin."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

FIELDS = ('alu', 'q', 'registers', 'test', 'next_pc', 'external_read')


def run(out=HERE / 'results/joint-mask04-receive-pulse-carryover.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if len(samples) != impulse.SAMPLES or samples[25] != 0x51:
        raise ValueError('reference ADC source changed')
    offered = dict(baseline=impulse.held_samples(samples, 25, None),
                   pulse=impulse.held_samples(samples, 25, 0xB1))
    cases = []
    scenarios = {}
    with tempfile.TemporaryDirectory() as tmp:
        paths = {}
        for name, adc in offered.items():
            scenario = configured(base, adc, 'previous', 'overflow', 1)
            scenarios[name] = scenario
            path = Path(tmp) / name
            result = execute(mapping, scenario, impulse.CYCLES,
                             mode='integrated', out=path,
                             trace_limit=impulse.CYCLES)
            if (not result['clean'] or
                    result['completed_cycles'] != impulse.CYCLES or
                    result['address_counts'].get(0x3F8) != impulse.ADC_VISITS or
                    result['edge_counts'].get('3ed->3ee', 0) != 0):
                raise ValueError(('receive trace stopped', name))
            paths[name] = path / 'trace.jsonl'
            cases.append(dict(input=name,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              trace_digest=result['trace_digest'],
                              completed_cycles=result['completed_cycles'],
                              final_state=result['final_state']))
            print(name, result['trace_digest'], flush=True)
        counts = Counter()
        state_counts = Counter()
        state_spans = {}
        by_pc = {}
        carryover = []
        after_rejoin_events = []
        adc_seen = 0
        last_pulse_3fe_cycle = None
        next_adc_cycle = None
        ram = {name: scenario['initial']['ram'][:]
               for name, scenario in scenarios.items()}
        with paths['baseline'].open() as left, paths['pulse'].open() as right:
            for left_line, right_line in zip(left, right):
                a, b = json.loads(left_line), json.loads(right_line)
                if a['cycle'] != b['cycle'] or a['pc'] != b['pc']:
                    raise ValueError(('program paths diverged', a['cycle'], b['cycle']))
                pc, cycle = a['pc'], a['cycle']
                if pc == 0x3F8:
                    adc_seen += 1
                    if adc_seen == 1220:
                        next_adc_cycle = cycle
                if (pc == 0x3FE and adc_seen == 1219 and
                        last_pulse_3fe_cycle is None):
                    last_pulse_3fe_cycle = cycle
                window = ('pulse_or_before' if last_pulse_3fe_cycle is None
                          or cycle <= last_pulse_3fe_cycle else
                          'carryover_before_next_adc' if next_adc_cycle is None
                          else 'after_next_adc')
                field_differences = [key for key in FIELDS if a[key] != b[key]]
                for key in field_differences:
                    counts[(window, key)] += 1
                    by_pc.setdefault(window, Counter())[(f'{pc:03X}', key)] += 1
                for name, row in (('baseline', a), ('pulse', b)):
                    for address, value in row['registers'].items():
                        ram[name][int(address)] = value
                flags_a = tuple(a['alu'][key] for key in ('carry', 'overflow',
                                                          'zero', 'sign'))
                flags_b = tuple(b['alu'][key] for key in ('carry', 'overflow',
                                                          'zero', 'sign'))
                state_diff = dict(ram=ram['baseline'] != ram['pulse'],
                                  q=a['q'] != b['q'],
                                  flags=flags_a != flags_b)
                for key, differs in state_diff.items():
                    if differs:
                        state_counts[(window, key)] += 1
                        span = state_spans.setdefault((window, key),
                                                      dict(first=cycle, last=cycle))
                        span['last'] = cycle
                if window == 'carryover_before_next_adc' and (field_differences
                                                                or any(state_diff.values())):
                    carryover.append(dict(cycle=cycle, pc=f'{pc:03X}',
                                          y=[a['alu']['y'], b['alu']['y']],
                                          q=[a['q'], b['q']],
                                          fields=field_differences,
                                          state_diff=state_diff))
                if window == 'after_next_adc' and field_differences:
                    after_rejoin_events.append(dict(cycle=cycle, pc=f'{pc:03X}',
                                                    fields=field_differences,
                                                    y=[a['alu']['y'], b['alu']['y']],
                                                    state_diff=state_diff))
        if (adc_seen != impulse.ADC_VISITS or
                last_pulse_3fe_cycle is None or next_adc_cycle is None or
                cases[0]['final_state'] != cases[1]['final_state']):
            raise ValueError('pulse comparison did not reconverge')
        last_post_state_difference = max(
            (span['last'] for (window, _), span in state_spans.items()
             if window == 'after_next_adc'), default=None)
        last_post_event_difference = max(
            (row['cycle'] for row in after_rejoin_events), default=None)
        first_full_rejoin_cycle = max(last_post_state_difference,
                                      last_post_event_difference) + 1
    paths = (Path(__file__), Path(impulse.__file__),
             HERE.parent / 'assumed/execute.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(
        experiment='full real-PROM trace difference around one matched-tail ADC pulse',
        fixture=dict(pulse_sample=25, base_adc=0x51, pulse_adc=0xB1,
                     samples=impulse.SAMPLES, adc_visits=impulse.ADC_VISITS,
                     cycles=impulse.CYCLES,
                     row3_end_cycle=last_pulse_3fe_cycle,
                     first_next_adc_cycle=next_adc_cycle,
                     first_full_rejoin_cycle=first_full_rejoin_cycle),
        cases=cases,
        field_difference_counts={window: {field: counts[(window, field)]
                                          for field in FIELDS}
                                 for window in ('pulse_or_before',
                                                'carryover_before_next_adc',
                                                'after_next_adc')},
        state_difference_counts={window: {field: state_counts[(window, field)]
                                          for field in ('ram', 'q', 'flags')}
                                 for window in ('pulse_or_before',
                                                'carryover_before_next_adc',
                                                'after_next_adc')},
        state_difference_spans={window: {
            field: state_spans.get((window, field))
            for field in ('ram', 'q', 'flags')}
            for window in ('carryover_before_next_adc', 'after_next_adc')},
        field_differences_by_pc={window: {f'{pc}:{field}': count
                                          for (pc, field), count in sorted(
                                              by_pc.get(window, {}).items())}
                                 for window in ('carryover_before_next_adc',
                                                'after_next_adc')},
        carryover_rows=carryover,
        after_rejoin_events=after_rejoin_events,
        limitations=[
            'The mapping, ADC ingress, four-row dispatch and TEST source remain hypotheses.',
            'A transient difference before the next ADC read is not a recovered symbol decision.',
            'The trace comparison is for one varying waveform and one high-nibble pulse.'
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
