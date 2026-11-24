"""Execute photo-candidate distinct Am2901 slice instructions with real PROMs."""
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
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

PHOTO_LINK = HERE / 'results/photo-slice-link.json'
LINKS = {'4': 1, '6': 2}
OUTPUT_PCS = tuple(range(0x392, 0x3A0))


def split_scenario(base, undriven=0):
    scenario = copy.deepcopy(base)
    scenario['name'] += f'; U8 instruction links I4=U2.I1, I6=U2.I2; undriven shift={undriven}'
    scenario['inputs']['slice_instruction'] = dict(
        high_from_low=LINKS, status='hypothesis',
        evidence='Two facing-pad candidates in g2/PHOTO-SLICE-LINK.md; '
                 'ordinary carry and shift cascade remains assumed.',
        undriven_shift=dict(value=undriven, status='stub',
                            evidence='Diagnostic level when one slice requests a shift bit '
                                     'that the other slice does not drive.'))
    return scenario


def stream_case(mapping, scenario, cycles, directory):
    result = execute(mapping, scenario, cycles, mode='integrated',
                     out=directory, trace_limit=cycles)
    trace = [json.loads(line) for line in (directory / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != cycles:
        raise ValueError('controller-fed split-slice run did not complete')
    inputs = [row for row in trace if row['pc'] == 0x38E]
    if any(row['external_read']['held_last'] for row in inputs):
        raise ValueError('controller bit sequence ran out')
    first = inputs[0]['cycle'] if inputs else cycles
    reads = [row['external_read']['address'] for row in trace
             if row['cycle'] > first and row.get('external_read', {}).get('selected_by_alu')
             and 'address' in row['external_read']]
    outputs = defaultdict(set)
    for row in trace:
        if row['cycle'] > first and row['pc'] in OUTPUT_PCS:
            outputs[f'{row["pc"]:03X}'].add(row['alu']['y'])
    return dict(clean=True, input_visits=len(inputs),
                selected_rom_reads_after_first_input=len(reads),
                distinct_rom_addresses_after_first_input=len(set(reads)),
                output_y_by_site={site: sorted(values) for site, values in sorted(outputs.items())},
                variable_output_sites=sorted(site for site, values in outputs.items()
                                             if len(values) > 1),
                final_pc=f'{result["final_state"]["pc"]:03X}',
                register_changes=result['register_changes'],
                undriven_shift_reads=result.get('undriven_shift_reads', 0),
                trace_digest=result['trace_digest'])


def run(out):
    photo = json.loads(PHOTO_LINK.read_text())
    if [row['id'] for row in photo['visible_segments']['segments']] != ['I4-I1', 'I6-I2']:
        raise ValueError('photo link evidence changed')
    _, base = fixture()
    _, bits = controller_stream()
    base['io']['read']['pc_sequences']['910'] = bits
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for name, path in MAPPINGS.items():
            mapping = mapped(path)
            scenario = split_scenario(base)
            sweep = []
            for q in range(256):
                scenario['initial']['q'] = q
                result = execute(mapping, scenario, 512, mode='integrated', trace_limit=0)
                if not result['clean']:
                    raise ValueError(f'{name} Q={q}: split run did not complete')
                sweep.append(dict(q=q, selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                  input_visits=result['address_counts'].get(0x38E, 0),
                                  output_visits=sum(result['address_counts'].get(pc, 0)
                                                    for pc in OUTPUT_PCS),
                                  undriven_shift_reads=result['undriven_shift_reads'],
                                  final_pc=f'{result["final_state"]["pc"]:03X}'))
            scenario['initial']['q'] = 5
            split0 = stream_case(mapping, scenario, 1580, directory / f'{name}-split0')
            split1_scenario = split_scenario(base, undriven=1)
            split1_scenario['initial']['q'] = 5
            split1 = stream_case(mapping, split1_scenario, 1580,
                                 directory / f'{name}-split1')
            shared_scenario = copy.deepcopy(base)
            shared_scenario['initial']['q'] = 5
            shared = stream_case(mapping, shared_scenario, 1580, directory / f'{name}-shared')
            rom_witness = None
            if name == 'q2':
                scenario['initial']['q'] = 0
                witness_dir = directory / 'q2-rom-witness'
                witness = execute(mapping, scenario, 512, mode='integrated',
                                  out=witness_dir, trace_limit=512)
                witness_trace = [json.loads(line) for line in
                                 (witness_dir/'trace.jsonl').read_text().splitlines()]
                reads = [(row['pc'], row['external_read']['address'],
                          row['external_read']['value'], row['alu']['y'])
                         for row in witness_trace
                         if row.get('external_read', {}).get('selected_by_alu')
                         and 'address' in row['external_read']]
                if not witness['clean'] or len(reads) != 118:
                    raise ValueError('q2 split-slice ROM witness changed')
                rom_witness = dict(initial_q=0, cycles=512, selected_reads=len(reads),
                                   distinct_pc=sorted({f'{pc:03X}' for pc, _, _, _ in reads}),
                                   distinct_addresses=sorted({a for _, a, _, _ in reads}),
                                   distinct_rom_values=sorted({v for _, _, v, _ in reads}),
                                   distinct_y=sorted({y for _, _, _, y in reads}),
                                   undriven_shift_reads=witness['undriven_shift_reads'],
                                   trace_digest=witness['trace_digest'])
            cases.append(dict(mapping=name, seed_sweep=dict(
                                  runs=len(sweep),
                                  active_input_q=[row['q'] for row in sweep if row['input_visits'] > 2],
                                  active_output_q=[row['q'] for row in sweep if row['output_visits'] > 2],
                                  q_with_undriven_shift=[row['q'] for row in sweep
                                                         if row['undriven_shift_reads']],
                                  max_undriven_shift_reads=max(row['undriven_shift_reads']
                                                               for row in sweep),
                                  max_selected_rom_reads=max(row['selected_rom_reads'] for row in sweep),
                                  q_at_max_rom=[row['q'] for row in sweep if row['selected_rom_reads'] ==
                                                max(r['selected_rom_reads'] for r in sweep)]),
                              controller_stream=dict(shared=shared, split_undriven_0=split0,
                                                     split_undriven_1=split1),
                              rom_witness=rom_witness))
    sources = [Path(__file__), PHOTO_LINK, HERE/'photo_controller_path.py',
               HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
               HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
               HERE.parent/'model.py', *MAPPINGS.values()]
    report = dict(status='photo-candidate split-slice execution, not recovered board wiring',
                  stimulus=dict(controller_bits_offered=len(bits),
                                q_seeds_per_mapping=256, seed_cycles=512,
                                seed_undriven_shift=0, stream_q=5, stream_cycles=1580,
                                stream_undriven_shift_levels=[0, 1]),
                  slice_instruction=dict(high_from_low=LINKS,
                                         carry_and_shift='ordinary eight-bit cascade, hypothetical; undriven cross-slice shift inputs explicitly stubbed'),
                  cases=cases,
                  limitations=['The two photo segments have pad gaps and do not prove continuity.',
                               'Only two high-slice instruction bits differ; remaining control pins, carry and shifts are assumptions.',
                               'ALU Y at listed PCs is not a traced DAC byte or line signal.'],
                  source_sha256={str(path.resolve().relative_to(HERE.parents[2].resolve())):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/split-slice-probe.json')
    print([(row['mapping'], row['seed_sweep']['max_selected_rom_reads'],
            row['controller_stream']['split_undriven_0']['variable_output_sites'],
            row['controller_stream']['split_undriven_1']['variable_output_sites'])
           for row in report['cases']])
