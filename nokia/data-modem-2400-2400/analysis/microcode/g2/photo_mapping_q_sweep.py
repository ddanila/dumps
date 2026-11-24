"""Sweep all initial Q bytes across five photo-compatible Am2901 mappings."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture
from photo_mapping_stream_screen import MAPPINGS


def mapped(path):
    mapping = json.loads(path.read_text())
    if mapping['fields']['a']['bits'] != ['18.1', '18.0', '17.7', '17.6']:
        raise ValueError(f'{path} A field changed')
    mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
    mapping['fields']['a']['status'] = 'hypothesis'
    mapping['fields']['a']['evidence'] = (
        'Photo candidate U10 D7/D6 through U5 Q1/Q2 to U2 A2/A3; '
        'not measured continuity.')
    return mapping


def run(out):
    _, base = fixture()
    _, bits = controller_stream()
    base['io']['read']['pc_sequences']['910'] = bits
    cases = []
    for name, path in MAPPINGS.items():
        mapping = mapped(path)
        scenario = copy.deepcopy(base)
        rows = []
        for q in range(256):
            scenario['initial']['q'] = q
            result = execute(mapping, scenario, 512, mode='integrated', trace_limit=0)
            rows.append(dict(q=q, clean=result['clean'],
                             input_38e=result['address_counts'].get(0x38e, 0),
                             output_392=result['address_counts'].get(0x392, 0),
                             output_396=result['address_counts'].get(0x396, 0),
                             selected_rom_reads=result['rom_reads']['selected_by_alu'],
                             final_pc=f'{result["final_state"]["pc"]:03X}'))
        if any(not row['clean'] for row in rows):
            raise ValueError(f'{name} startup sweep stopped')
        active = [row['q'] for row in rows if row['input_38e'] > 2]
        many_rom = [row['q'] for row in rows if row['selected_rom_reads'] > 10]
        output = [row['q'] for row in rows if max(row['output_392'], row['output_396']) > 2]
        cases.append(dict(mapping=name, runs=len(rows), clean_runs=len(rows),
                          active_input_q=active, many_rom_q=many_rom,
                          candidate_output_q=output,
                          final_pc_counts=dict(sorted(Counter(row['final_pc'] for row in rows).items())),
                          rows=rows))
    if ([len(c['active_input_q']) for c in cases] != [32]*5 or
            [len(c['many_rom_q']) for c in cases] != [0, 32, 0, 1, 0]):
        raise ValueError('startup path classes changed')

    q2 = mapped(MAPPINGS['q2'])
    witnesses = []
    with tempfile.TemporaryDirectory() as temporary:
        scenario = copy.deepcopy(base)
        for q in range(0, 256, 8):
            scenario['initial']['q'] = q
            target = Path(temporary)/str(q)
            result = execute(q2, scenario, 512, mode='integrated',
                             out=target, trace_limit=512)
            trace = [json.loads(line) for line in (target/'trace.jsonl').read_text().splitlines()]
            repeated = [row for row in trace if row['pc'] == 0x129 and
                        row.get('external_read', {}).get('selected_by_alu')]
            addresses = sorted({row['external_read']['address'] for row in repeated})
            values = sorted({row['alu']['y'] for row in repeated})
            if (not result['clean'] or len(repeated) != 118 or
                    addresses != [0x100 + q + 1] or len(values) != 1 or
                    result['address_counts'].get(0x38e, 0)):
                raise ValueError(f'q2 Q={q} repeated ROM path changed')
            witnesses.append(dict(initial_q=q, read_pc='129', reads=len(repeated),
                                  address=addresses[0], alu_y=values[0],
                                  input_38e_visits=0, trace_digest=result['trace_digest']))
    paths = [Path(__file__), HERE/'photo_mapping_stream_screen.py',
             HERE/'photo_controller_path.py', HERE/'controller_bit_dispatch.py',
             ASSUMED/'execute.py', HERE.parent/'model.py',
             HERE/'results/swapped-sine-loop/phase-20-scenario.json',
             HERE/'photo-i7-constraint.json', HERE/'photo-a-input-constraint.json',
             *MAPPINGS.values()]
    report = dict(status='photo-constrained startup-state screen, not physical execution',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths},
                  fixture=dict(cycles_per_seed=512, initial_ram=[0]*16,
                               offered_controller_bits=len(bits), candidate_input_pc='38E',
                               q_values=256, mappings=list(MAPPINGS)),
                  cases=cases, q2_fixed_rom_witnesses=witnesses,
                  limitations=['The same q3-derived branch, condition, ROM and input fixture is reused across all mappings.',
                               'Q is swept independently at reset; actual power-on and mode-initialized values are unknown.',
                               'A repeated ROM read is not a transmitter without symbol dependence, sample timing and physical output routing.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-mapping-q-sweep.json')
    print([(c['mapping'], len(c['active_input_q']), len(c['many_rom_q']),
            len(c['candidate_output_q'])) for c in report['cases']])
