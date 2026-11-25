"""Screen a candidate ADC D bus hold through wrapper PC 3EB."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import codes, scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

VISITS = 3000
CYCLES = 16 * VISITS + 47
HELD = (0x00, 0x01, 0x09, 0x19, 0x59, 0xA9, 0xFF)


def scenario(base, at_3eb, at_3f8, visits):
    candidate = scenario_for_full_byte(
        base, visits if at_3f8 else [0x09] * VISITS, 'complementary')
    candidate['dispatch']['mode'] = 'sequence'
    candidate['dispatch']['sequence'] = [0, 2]
    if at_3eb:
        # The wrapper visits 3EB twice per 3F8 ADC visit, plus once at the
        # final boundary. Both visits see the same held converter byte.
        candidate['io']['read']['pc_sequences'][str(0x3EB)] = [
            value for value in visits for _ in range(2)] + [visits[-1]]
        candidate['io']['read']['evidence'] += (
            '; hypothetical ADC D bus also held at wrapper 3EB; '
            'two wrapper visits per 3F8 visit')
    return candidate


def run_case(mapping, base, label, visits, at_3eb, at_3f8):
    result = execute(mapping, scenario(base, at_3eb, at_3f8, visits),
                     CYCLES, mode='integrated', trace_limit=0)
    if not result['clean'] or result['completed_cycles'] != CYCLES:
        raise ValueError(('ADC wrapper scenario stopped', label))
    counts = result['address_counts']
    return dict(label=label, at_3eb=at_3eb, at_3f8=at_3f8,
                pc_3eb_visits=counts.get(0x3EB, 0),
                pc_3f8_visits=counts.get(0x3F8, 0),
                selected_3eb_reads=result['read_sequence_visits'].get(0x3EB, 0),
                selected_3f8_reads=result['read_sequence_visits'].get(0x3F8, 0),
                final_pc=f'{result["final_state"]["pc"]:03X}',
                trace_digest=result['trace_digest'])


def first_wrapper_branch(mapping, base, level):
    with tempfile.TemporaryDirectory() as temporary:
        execute(mapping, scenario(base, True, False, [level] * VISITS),
                70, mode='integrated', out=temporary, trace_limit=70)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').open()]
    first_3eb = next(row for row in trace if row['pc'] == 0x3EB)
    first_3ed = next(row for row in trace if row['pc'] == 0x3ED)
    return dict(level=f'{level:02X}', y_3eb=first_3eb['alu']['y'],
                test_3ed=first_3ed['test'],
                next_pc_after_3ed=f'{first_3ed["next_pc"]:03X}')


def run(out=HERE / 'results/receiver-3eb-adc-route-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    held = [run_case(mapping, base, f'{value:02X}', [value] * VISITS,
                     True, False) for value in HELD]
    samples = codes((0, 1, 3, 2), 32, 'complementary')
    visits = [value for sample, value in enumerate(samples)
              for _ in range(94 if sample % 4 < 3 else 93)]
    if len(visits) != VISITS:
        raise ValueError('two-row sample hold changed')
    waveform = [run_case(mapping, base, name, visits, at_3eb, at_3f8)
                for name, at_3eb, at_3f8 in
                (('3F8 only', False, True), ('3EB only', True, False),
                 ('3EB and 3F8', True, True))]
    if ([row['pc_3f8_visits'] for row in waveform] != [3000, 282, 282] or
            [row['pc_3f8_visits'] for row in held if row['label'] in ('A9', 'FF')]
            != [0, 0]):
        raise ValueError('ADC wrapper outcome changed')
    report = dict(experiment='hypothetical ADC D bus held through 3EB wrapper',
                  fixture=dict(dispatch='scenario [0,2] at 3EC',
                               mapping='joint upper-source mask 08',
                               adc_coding='complementary 127 minus reference PCM',
                               wrapper_holds='two 3EB visits per 3F8 visit',
                               waveform_first_codes=[f'{value:02X}'
                                                     for value in samples[:8]],
                               total_cycles=CYCLES),
                  held=held, waveform=waveform,
                  initial_wrapper_branches=[first_wrapper_branch(mapping, base, value)
                                            for value in (0x09, 0xA9)],
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(row['label'], row['pc_3f8_visits']) for row in result['waveform']])
