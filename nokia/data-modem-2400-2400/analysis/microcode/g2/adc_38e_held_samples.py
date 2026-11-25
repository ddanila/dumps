"""Replay ADC0800-like bytes held for one 9600-sample/s interval at D38E."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]

from common import save
from execute import execute
from adc_sample_path import DIBITS
from controller_bit_dispatch import groups_for, post_group_states
from photo_controller_path import fixture
from reference_modem import receive, transmit

SAMPLE_HZ = 9600
OSC_HZ = 14_400_000
INSTRUCTIONS_PER_VISIT = 12
VISITS_PER_SAMPLE = OSC_HZ // SAMPLE_HZ // INSTRUCTIONS_PER_VISIT
PREFIX_SAMPLES = 16
SHARED_SAMPLES = 4


def run(out=HERE / 'results/adc-38e-held-samples.json'):
    if VISITS_PER_SAMPLE != 125:
        raise ValueError('nonintegral sample hold')
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference waveform is not decodable')
    complement = [127 - value for value in pcm]
    prefix = complement[64:64 + PREFIX_SAMPLES]
    shared = complement[80:80 + SHARED_SAMPLES]
    sample_sequences = [('forward_prefix', prefix + shared),
                        ('reverse_prefix', prefix[::-1] + shared)]
    if prefix == prefix[::-1] or len(set(prefix)) < 4:
        raise ValueError('sample histories did not differ')
    mapping, base = fixture()
    base['initial']['q'] = 5
    cases = []
    histories = []
    for name, samples in sample_sequences:
        offered = [value for sample in samples
                   for value in [sample] * VISITS_PER_SAMPLE]
        scenario = copy.deepcopy(base)
        scenario['name'] += f'; held ADC sample history {name}'
        scenario['io']['read']['pc_sequences'][str(0x38e)] = offered
        scenario['io']['read']['evidence'] += (
            '; candidate ADC0800 complementary bytes held for 125 D38E visits; '
            'physical bus and timing untraced')
        cycles = INSTRUCTIONS_PER_VISIT * len(offered) + 44
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        reads = [row for row in trace if row['pc'] == 0x38e]
        if (not result['clean'] or result['completed_cycles'] != cycles or
                len(reads) != len(offered) or
                [row['external_read']['value'] for row in reads] != offered or
                not all(row['external_read']['selected_by_alu'] for row in reads)):
            raise ValueError(('ADC hold stream not consumed', name))
        groups = groups_for(trace)
        states = post_group_states(trace, scenario['initial']['ram'])
        if len(groups) != len(offered) or len(states) != len(offered):
            raise ValueError(('dispatch groups missing', name))
        first_dispatch = groups[0]['cycle']
        later_rom_reads = sum(row['cycle'] > first_dispatch and
                              row.get('external_read', {}).get('selected_by_alu') and
                              'address' in row['external_read'] for row in trace)
        histories.append(states)
        cases.append(dict(name=name, sample_codes=samples,
                          d38e_visits=len(reads), microinstructions=cycles,
                          distinct_codes=len(set(samples)),
                          post_dispatch_rom_reads=later_rom_reads,
                          first_shared_group_index=PREFIX_SAMPLES * VISITS_PER_SAMPLE,
                          final_state_sha256=hashlib.sha256(json.dumps(
                              result['final_state'], sort_keys=True).encode()).hexdigest(),
                          trace_digest=result['trace_digest']))
    differences = [index for index, (first, second) in
                   enumerate(zip(*histories)) if first != second]
    shared_start = PREFIX_SAMPLES * VISITS_PER_SAMPLE
    if (not differences or max(differences) >= shared_start or
            cases[0]['final_state_sha256'] != cases[1]['final_state_sha256'] or
            any(case['post_dispatch_rom_reads'] for case in cases)):
        raise ValueError(('candidate receive history persisted',
                          differences[-10:], cases))
    paths = [Path(__file__), HERE / 'adc_sample_path.py',
             HERE / 'controller_bit_dispatch.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE / 'ADC0800-INPUT.md',
             ASSUMED / 'execute.py']
    report = dict(status='held ADC-like samples at D38E leave no modeled receive history after the first shared input group',
                  fixture=dict(mapping=mapping['name'], initial_q=5,
                               adc_code='127 - reference signed PCM',
                               candidate_input_pc='38E', oscillator_hz=OSC_HZ,
                               microinstruction_divisor=1, sample_hz=SAMPLE_HZ,
                               instructions_per_d38e_visit=INSTRUCTIONS_PER_VISIT,
                               d38e_visits_per_sample=VISITS_PER_SAMPLE,
                               first_reference_sample_index=64,
                               prefix_samples=PREFIX_SAMPLES,
                               shared_tail_samples=SHARED_SAMPLES),
                  cases=cases, differing_group_count=len(differences),
                  last_differing_group_index=max(differences),
                  first_shared_group_index=shared_start,
                  identical_after_first_shared_group=True,
                  limitations=['ADC-to-D38E wiring, reference range, Q seed, microcycle divisor and conversion schedule are hypotheses.',
                               'This comparison covers the modeled 38E dispatch path, not another DSC input site or external RAM state.',
                               'No recovered bits reach the USART; C3 is not met.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['differing_group_count'], report['last_differing_group_index'],
          report['first_shared_group_index'])
