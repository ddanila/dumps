"""Feed continuous-controller USART bytes into a candidate DSC2847 D input."""

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
from common import read, save
from execute import execute
from controller_bit_dispatch import groups_for, post_group_states
from photo_controller_path import (BASE_MAPPING, BASE_SCENARIO, GATE_FITS, INPUT_PC,
                                   PHOTO_A_RECORD, PHOTO_RECORD, fixture)

CONTROLLER = HERE / 'results/main-loop-serial.json'
SAMPLE_CYCLES_PER_BIT = 12
STARTUP_AND_FINAL_CYCLES = 44


def run(out):
    source = read(CONTROLLER)
    if len(source['rows']) != 256 or source['distinct_streams'] != 4:
        raise ValueError('controller line-stream report changed')
    representatives = [(group['selectors'][0], group['line_bytes'])
                       for group in source['groups']]
    if [name for name, _ in representatives] != ['00', '20', '40', '60']:
        raise ValueError('controller stream groups changed')
    streams = representatives + [('combined', [byte for _, values in representatives
                                              for byte in values])]
    mapping, base = fixture()
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for name, values in streams:
            bits = [(byte >> bit) & 1 for byte in values for bit in range(8)]
            scenario = copy.deepcopy(base)
            scenario['name'] += f'; continuous-controller line stream {name} at D38E'
            scenario['initial']['q'] = 5
            scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = bits
            scenario['io']['read']['evidence'] = (
                'LSB-first bytes written by unchanged 8031 main-loop ROM to USART data '
                'address 01 under the saved diagnostic status/timer fixture; connection '
                'to DSC2847 D38E is a hypothesis.')
            cycles = SAMPLE_CYCLES_PER_BIT * len(bits) + STARTUP_AND_FINAL_CYCLES
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=path, trace_limit=cycles)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
            reads = [row['external_read']['value'] for row in trace if row['pc'] == INPUT_PC]
            groups = groups_for(trace)
            states = post_group_states(trace, scenario['initial']['ram'])
            if not result['clean'] or reads != bits or len(groups) != len(bits) or len(states) != len(bits):
                raise ValueError(f'incomplete controller-to-DSC execution: {name}')
            if [group['index'] for group in groups] != [((bit - 5) & 255) for bit in bits]:
                raise ValueError(f'dispatch differs from D-Q: {name}')
            first_dispatch = next(row['cycle'] for row in trace if row['pc'] == 0x38f)
            later_rom_reads = [row for row in trace if row['cycle'] > first_dispatch
                               and row.get('external_read', {}).get('selected_by_alu')
                               and 'address' in row['external_read']]
            by_bit = defaultdict(lambda: dict(groups=set(), states=set()))
            for bit, group, state in zip(bits, groups, states):
                by_bit[bit]['groups'].add(tuple(group['bytes']))
                by_bit[bit]['states'].add(json.dumps(state, sort_keys=True))
            cases.append(dict(stream=name, bytes=values, bit_order='LSB first', bits=len(bits),
                              zero_bits=bits.count(0), one_bits=bits.count(1),
                              cycles=cycles, clean=result['clean'],
                              input_reads=len(reads), dispatch_groups=len(groups),
                              group_by_bit={str(bit): [list(g) for g in sorted(by_bit[bit]['groups'])]
                                            for bit in (0, 1)},
                              distinct_post_group_states_by_bit={str(bit): len(by_bit[bit]['states'])
                                                                 for bit in (0, 1)},
                              later_rom_reads=len(later_rom_reads),
                              candidate_output_word_392=result['address_counts'].get(0x392, 0),
                              final_q=result['final_state']['q'],
                              final_pc=f"{result['final_state']['pc']:03X}",
                              trace_digest=result['trace_digest']))
            if name == 'combined':
                (out / 'witness-trace.jsonl').write_bytes((path / 'trace.jsonl').read_bytes())
                (out / 'witness-scenario.json').write_bytes((path / 'scenario.json').read_bytes())
                save(out / 'witness-mapping.json', mapping)
    source_paths = [Path(__file__), CONTROLLER, HERE / 'main_loop_serial.py',
                    HERE / 'main_loop_probe.c', HERE / 'photo_controller_path.py',
                    HERE / 'controller_bit_dispatch.py', BASE_MAPPING, BASE_SCENARIO,
                    PHOTO_RECORD, PHOTO_A_RECORD, GATE_FITS,
                    ASSUMED / 'execute.py', ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='controller-main-loop-bytes-in-candidate-DSC-path-not-G2-C2',
                  candidate_input_pc=f'{INPUT_PC:03X}', initial_q=5,
                  controller_rom_sha256=source['controller_rom_sha256'],
                  cases=cases,
                  limitations=['The 8031 USART-ready, receive and timer events are diagnostic fixtures.',
                               'One controller bit per DSC2847 D38E visit is an untraced connection and timing assumption.',
                               'The photo A/I routes, ROM enable and initial Q remain hypotheses.',
                               'ALU quartets are not traced to a physical line-output converter.',
                               'This does not demonstrate a transmitter, receiver or echo canceller.'],
                  source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source_paths})
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/main-loop-dsp-bridge')
    print(len(report['cases']), 'streams;', sum(c['bits'] for c in report['cases']),
          'candidate DSC input bits')
