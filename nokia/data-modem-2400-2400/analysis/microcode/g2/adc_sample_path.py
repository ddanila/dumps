"""Feed reference line samples as candidate ADC0800 bytes to DSC2847 D38E."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import groups_for, post_group_states
from photo_controller_path import fixture, INPUT_PC, DISPATCH_PC
from reference_modem import receive, transmit

DIBITS = [0] * 8 + [0, 1, 3, 2] * 4 + [0] * 8


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    pcm = transmit(DIBITS)
    reference_decisions = receive(pcm)
    if reference_decisions != DIBITS[1:]:
        raise ValueError('reference stimulus does not recover its dibits')
    mapping, base = fixture()
    base['initial']['q'] = 5
    cases = []
    for polarity, codes in [('adc_complementary', [127 - v for v in pcm]),
                            ('inverted_bus_alternative', [128 + v for v in pcm])]:
        order_maps = []
        for order, stream in [('forward', codes), ('reverse', codes[::-1])]:
            scenario = copy.deepcopy(base)
            scenario['name'] += f'; diagnostic {polarity} {order} line samples at D38E'
            scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = stream
            scenario['io']['read']['evidence'] += (
                '; ADC0800-INPUT.md motivates complementary sample codes; '
                'the ADC-to-D38E connection and reference range are hypotheses')
            cycles = 12 * len(stream) + 44
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                result = execute(mapping, scenario, cycles, mode='integrated',
                                 out=path, trace_limit=cycles)
                trace = [json.loads(line) for line in
                         (path / 'trace.jsonl').read_text().splitlines()]
                if polarity == 'adc_complementary' and order == 'forward':
                    for name in ('trace.jsonl', 'scenario.json', 'mapping.json'):
                        (out / f'witness-{name}').write_bytes((path / name).read_bytes())
            reads = [row['external_read']['value'] for row in trace
                     if row['pc'] == INPUT_PC]
            groups = groups_for(trace)
            states = post_group_states(trace, scenario['initial']['ram'])
            if (not result['clean'] or reads != stream or
                    len(groups) != len(stream) or len(states) != len(stream)):
                raise ValueError('sample stream was not consumed one byte per group')
            by_code = defaultdict(set)
            by_mod4 = defaultdict(set)
            for code, group, state in zip(stream, groups, states):
                signature = json.dumps(dict(index=group['index'],
                                            output=group['bytes'], state=state),
                                       sort_keys=True)
                by_code[code].add(signature)
                by_mod4[code & 3].add(tuple(group['bytes']))
            order_maps.append(by_code)
            first_dispatch = next(row['cycle'] for row in trace
                                  if row['pc'] == DISPATCH_PC)
            post_dispatch_rom_reads = sum(
                row['cycle'] > first_dispatch and
                row.get('external_read', {}).get('selected_by_alu') and
                'address' in row['external_read'] for row in trace)
            cases.append(dict(polarity=polarity, order=order,
                              clean=result['clean'], samples=len(stream),
                              distinct_input_codes=len(by_code),
                              max_states_per_code=max(map(len, by_code.values())),
                              output_groups_by_code_mod4={str(k): [list(v) for v in sorted(values)]
                                                          for k, values in sorted(by_mod4.items())},
                              post_dispatch_rom_reads=post_dispatch_rom_reads,
                              final_pc=f'{result["final_state"]["pc"]:03X}',
                              trace_digest=result['trace_digest']))
        if order_maps[0] != order_maps[1]:
            raise ValueError('same sample byte gave order-dependent post-group state')
    sources = [Path(__file__), HERE / 'reference_modem.py',
               HERE / 'photo_controller_path.py', HERE / 'controller_bit_dispatch.py',
               HERE / 'ADC0800-INPUT.md', ASSUMED / 'execute.py']
    report = dict(status='photo-candidate-ADC-path-not-C3',
                  dibits=DIBITS, signed_pcm=pcm,
                  reference_receive_errors=0,
                  adc_coding='diagnostic symmetric range: complementary=127-pcm; inverted alternative=128+pcm',
                  hypothetical_input_pc=f'{INPUT_PC:03X}',
                  initial_q=5, cases=cases,
                  same_byte_state_order_invariant=True,
                  source_sha256={str(p.relative_to(HERE.parents[2])):
                                 hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  limitations=[
                      'ADC0800 reference range and conversion schedule are diagnostic choices, not measured Nokia settings.',
                      'No physical net from ADC0800 to the DSC2847 D input at 38E has been traced.',
                      'The q1/q3 photo field routes, ROM gate, dispatch table and initial Q=5 are hypotheses.',
                      'Only the modeled state after one four-word group is compared; other paths or external state may retain history.',
                      'No recovered bit reaches the USART and C3 is not satisfied.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    result = run(HERE / 'results/adc-sample-path')
    print([(case['polarity'], case['order'], case['samples']) for case in result['cases']])
