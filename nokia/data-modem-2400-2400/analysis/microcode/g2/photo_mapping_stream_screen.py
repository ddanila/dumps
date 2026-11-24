"""Compare photo-compatible Am2901 mappings under one real controller bitstream."""
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

MAPPINGS = {name: HERE/f'results/photo-b-constraints/{name}-photo-swapped.json'
            for name in ('q1', 'q2', 'q3', 'q4')}
MAPPINGS['fitted_swapped'] = ASSUMED/'results/selector-completion/swapped-marked/mapping.json'


def run(out):
    _, base = fixture()
    _, bits = controller_stream()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        for name, path in MAPPINGS.items():
            mapping = json.loads(path.read_text())
            if mapping['fields']['a']['bits'] != ['18.1', '18.0', '17.7', '17.6']:
                raise ValueError(f'{name} no longer has swappable A field')
            mapping['name'] += '-photo-a2-a3-stream-screen'
            mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
            mapping['fields']['a']['status'] = 'hypothesis'
            mapping['fields']['a']['evidence'] = (
                'Photo candidate U10 D7/D6 through U5 Q1/Q2 to U2 A2/A3; '
                'not measured continuity.')
            scenario = copy.deepcopy(base)
            scenario['name'] += f'; {name} Q=5 controller stream'
            scenario['initial']['q'] = 5
            scenario['io']['read']['pc_sequences']['910'] = bits
            path_out = Path(temporary)/name
            result = execute(mapping, scenario, 1580, mode='integrated',
                             out=path_out, trace_limit=1580)
            trace = [json.loads(line) for line in
                     (path_out/'trace.jsonl').read_text().splitlines()]
            inputs = [row for row in trace if row['pc'] == 0x38E]
            if not result['clean'] or [row['external_read']['value'] for row in inputs] != bits:
                raise ValueError(f'{name} did not consume controller stream')
            first_cycle = inputs[0]['cycle']
            outputs, rom = defaultdict(list), defaultdict(list)
            for row in trace:
                if row['cycle'] <= first_cycle:
                    continue
                pc = f'{row["pc"]:03X}'
                outputs[pc].append(row['alu']['y'])
                read = row.get('external_read', {})
                if read.get('selected_by_alu') and 'address' in read:
                    rom[pc].append(read['address'])
            recurring = {pc: dict(visits=len(values), distinct_y=sorted(set(values)))
                         for pc, values in sorted(outputs.items()) if len(values) > 2}
            cases.append(dict(mapping=name, clean=True, input_bits=len(inputs),
                              recurring_pc_count=len(recurring),
                              variable_recurring_pcs={pc: row for pc, row in recurring.items()
                                                      if len(row['distinct_y']) > 1},
                              rom_after_first_input={pc: dict(visits=len(values),
                                                              addresses=sorted(set(values)))
                                                     for pc, values in sorted(rom.items())},
                              candidate_output_y={pc: sorted(set(outputs[pc]))
                                                  for pc in ('392', '396') if outputs[pc]},
                              visits_392=result['address_counts'].get(0x392, 0),
                              visits_396=result['address_counts'].get(0x396, 0),
                              final_pc=f'{result["final_state"]["pc"]:03X}',
                              trace_digest=result['trace_digest']))
    if ([sorted(case['variable_recurring_pcs']) for case in cases] !=
            [['38E'], [], ['38E'], [], []] or
            any(case['rom_after_first_input'] for case in cases)):
        raise ValueError('cross-mapping recurrent behavior changed')
    paths = [Path(__file__), HERE/'photo_controller_path.py',
             HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
             HERE.parent/'model.py',
             HERE/'results/swapped-sine-loop/phase-20-scenario.json',
             HERE/'photo-i7-constraint.json', HERE/'photo-a-input-constraint.json',
             *MAPPINGS.values()]
    report = dict(status='scoped cross-mapping controller screen, not recovered wiring',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths},
                  stimulus=dict(controller_bits=len(bits), initial_q=5, initial_ram=[0]*16,
                                hypothetical_d_pc='38E', cycles=1580),
                  cases=cases,
                  limitations=['The same q3-derived branch, ROM, condition and input fixture is reused across five ALU mappings.',
                               'The photo-derived A2/A3 and E4/E2 routes are candidates, not measured wiring.',
                               'No physical DAC output or sample clock is identified; this excludes only the scoped Q=5 path.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-mapping-stream-screen.json')
    print([(row['mapping'], sorted(row['variable_recurring_pcs']),
            sorted(row['rom_after_first_input'])) for row in report['cases']])
