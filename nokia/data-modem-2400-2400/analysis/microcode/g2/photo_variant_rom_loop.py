"""Execute q1/q2 photo candidates through all gates selecting ROM D at 127."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from photo_controller_path import fixture, GATE_FITS, PHOTO_A_RECORD, PHOTO_RECORD

MAPPINGS = {name: HERE / f'results/photo-b-constraints/{name}-photo-swapped.json'
            for name in ('q1', 'q2')}
ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
CYCLES = 2048


def recurrence(rows):
    pairs = [(row['external_read']['address'], row['alu']['y']) for row in rows]
    seen = {}
    for index, pair in enumerate(pairs):
        if pair in seen:
            start = seen[pair]
            period = index - start
            exact = all(pairs[i] == pairs[i-period]
                        for i in range(index, len(pairs)))
            return dict(preperiod=start, period=period, exact_to_end=exact,
                        cycle_addresses=[address for address, _ in pairs[start:index]],
                        cycle_y=[value for _, value in pairs[start:index]])
        seen[pair] = index
    return dict(preperiod=None, period=None, exact_to_end=False,
                cycle_addresses=[], cycle_y=[])


def rom_feedback_basins(data, bank):
    """Classify x -> ROM[bank+x+1], stopping when x reaches zero."""
    basins = {}
    for seed in range(256):
        seen = {}
        value = seed
        while value not in seen and value != 0:
            seen[value] = len(seen)
            value = data[bank + ((value + 1) & 255)]
        if value == 0:
            key = ('zero', len(seen))
        else:
            cycle = []
            while value not in cycle:
                cycle.append(value)
                value = data[bank + ((value + 1) & 255)]
            key = ('cycle', tuple(sorted(cycle)))
        basins.setdefault(key, []).append(seed)
    return [dict(kind=key[0], steps_to_zero=key[1] if key[0] == 'zero' else None,
                 cycle_values=list(key[1]) if key[0] == 'cycle' else [],
                 seeds=seeds) for key, seeds in basins.items()]


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    gates = [gate for gate in read(GATE_FITS)['fits'] if 0x127 in gate['pcs']]
    if len(gates) != 16:
        raise ValueError('expected 16 diagnostic gates selecting 127')
    _, base = fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for name, mapping_path in MAPPINGS.items():
            mapping = read(mapping_path)
            if mapping['fields']['a']['bits'] != ['18.1', '18.0', '17.7', '17.6']:
                raise ValueError('base A field changed')
            mapping['name'] += '-photo-a2-a3'
            mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
            mapping['fields']['a']['status'] = 'hypothesis'
            mapping['fields']['a']['evidence'] = (
                'photo-a-input-constraint.json candidate U10 D7/D6 through '
                'U5 Q1/Q2 to U2 A2/A3')
            for gate_index, gate in enumerate(gates):
                scenario = copy.deepcopy(base)
                scenario['name'] += f'; {name} ROM gate {gate["terms"]}'
                scenario['io']['read']['address']['pcs'] = gate['pcs']
                result = execute(mapping, scenario, CYCLES, mode='integrated',
                                 out=path, trace_limit=CYCLES)
                trace = [json.loads(line) for line in
                         (path / 'trace.jsonl').read_text().splitlines()]
                sites = {}
                for pc in (0x127, 0x12C):
                    rows = [row for row in trace if row['pc'] == pc]
                    selected = [row for row in rows if
                                row.get('external_read', {}).get('selected_by_alu')
                                and 'address' in row['external_read']]
                    address_feedback = all(
                        selected[i]['external_read']['address'] ==
                        0x100 + ((selected[i-1]['alu']['y'] + 1) & 255)
                        for i in range(1, len(selected))) if len(selected) > 1 else None
                    sites[f'{pc:03X}'] = dict(visits=len(rows), rom_reads=len(selected),
                        distinct_rom_addresses=len({row['external_read']['address']
                                                    for row in selected}),
                        distinct_alu_y=len({row['alu']['y'] for row in rows}),
                        last_16_alu_y=[row['alu']['y'] for row in rows[-16:]],
                        address_is_prev_y_plus_one_upper_bank=address_feedback,
                        recurrence=recurrence(selected))
                cases.append(dict(mapping=name, gate_index=gate_index,
                                  gate_terms=gate['terms'], clean=result['clean'],
                                  final_pc=f'{result["final_state"]["pc"]:03X}',
                                  final_q=result['final_state']['q'], sites=sites,
                                  trace_digest=result['trace_digest']))
                if name == 'q1' and gate_index == 0:
                    for filename in ('trace.jsonl', 'mapping.json', 'scenario.json'):
                        (out / f'q1-witness-{filename}').write_bytes(
                            (path / filename).read_bytes())
    if any(not case['clean'] for case in cases):
        raise ValueError('photo variant ROM loop model stopped')
    rom = ROM.read_bytes()
    if len(rom) != 512:
        raise ValueError('Am27S31 dump size changed')
    basins = {str(bank): rom_feedback_basins(rom, bank) for bank in (0, 256)}
    q1_mapping = read(MAPPINGS['q1'])
    q1_mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
    zero_exit = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for value in (0, 1):
            scenario = copy.deepcopy(base)
            scenario['io']['read']['address']['pcs'] = [pc for pc in gates[0]['pcs']
                                                         if pc != 0x12C]
            scenario['io']['read']['pc_sequences']['300'] = [value]
            scenario['name'] += f'; diagnostic D12C={value} replaces ROM read'
            result = execute(q1_mapping, scenario, 128, mode='integrated',
                             out=path, trace_limit=128)
            trace = [json.loads(line) for line in
                     (path / 'trace.jsonl').read_text().splitlines()]
            first_blt = next(row for row in trace if row['pc'] == 0x12F)
            zero_exit.append(dict(value=value, clean=result['clean'],
                                  first_blt_test=first_blt['test'],
                                  first_blt_next_pc=f'{first_blt["next_pc"]:03X}',
                                  visits_12c=sum(row['pc'] == 0x12C for row in trace),
                                  visits_130=sum(row['pc'] == 0x130 for row in trace),
                                  trace_digest=result['trace_digest']))
            if value == 0:
                (out / 'q1-zero-exit-trace.jsonl').write_bytes(
                    (path / 'trace.jsonl').read_bytes())
                (out / 'q1-zero-exit-scenario.json').write_bytes(
                    (path / 'scenario.json').read_bytes())
    lower_scenario = copy.deepcopy(base)
    lower_scenario['name'] += '; q1 lower Am27S31 bank candidate'
    lower_scenario['io']['read']['address']['pcs'] = gates[0]['pcs']
    lower_scenario['io']['read']['address']['bank'] = 0
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        lower_result = execute(q1_mapping, lower_scenario, 128, mode='integrated',
                               out=path, trace_limit=128)
        lower_trace = [json.loads(line) for line in
                       (path / 'trace.jsonl').read_text().splitlines()]
        lower_reads = [row for row in lower_trace if row['pc'] == 0x12C]
        lower_blt = next(row for row in lower_trace if row['pc'] == 0x12F)
        for filename in ('trace.jsonl', 'scenario.json'):
            (out / f'q1-lower-bank-{filename}').write_bytes(
                (path / filename).read_bytes())
    lower_bank_probe = dict(clean=lower_result['clean'],
        reads_12c=len(lower_reads),
        first_rom_address=lower_reads[0]['external_read']['address'],
        first_rom_value=lower_reads[0]['external_read']['value'],
        first_blt_next_pc=f'{lower_blt["next_pc"]:03X}',
        visits_130=sum(row['pc'] == 0x130 for row in lower_trace),
        final_pc=f'{lower_result["final_state"]["pc"]:03X}',
        trace_digest=lower_result['trace_digest'])
    mixed_bank_probes = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for bank_127 in (0, 256):
            for bank_12c in (0, 256):
                scenario = copy.deepcopy(base)
                scenario['name'] += f'; A8 site candidates 127={bank_127} 12C={bank_12c}'
                address = scenario['io']['read']['address']
                address['pcs'] = gates[0]['pcs']
                address['bank'] = 256
                address['bank_by_pc'] = {str(0x127): bank_127,
                                         str(0x12C): bank_12c}
                address['evidence'] += ('; per-PC A8 choices are diagnostic '
                                        'candidates, not traced board wiring')
                result = execute(q1_mapping, scenario, 128, mode='integrated',
                                 out=path, trace_limit=128)
                trace = [json.loads(line) for line in
                         (path / 'trace.jsonl').read_text().splitlines()]
                reads = {pc: [row for row in trace if row['pc'] == pc and
                              row.get('external_read', {}).get('selected_by_alu')]
                         for pc in (0x127, 0x12C)}
                blt = next(row for row in trace if row['pc'] == 0x12F)
                mixed_bank_probes.append(dict(bank_127=bank_127, bank_12c=bank_12c,
                    clean=result['clean'],
                    first_reads={f'{pc:03X}': dict(address=reads[pc][0]['external_read']['address'],
                                                  value=reads[pc][0]['external_read']['value'])
                                 for pc in reads},
                    visits_12c=len(reads[0x12C]),
                    first_blt_next_pc=f'{blt["next_pc"]:03X}',
                    visits_130=sum(row['pc'] == 0x130 for row in trace),
                    final_pc=f'{result["final_state"]["pc"]:03X}',
                    trace_digest=result['trace_digest']))
                if bank_127 == 256 and bank_12c == 0:
                    for filename in ('trace.jsonl', 'scenario.json'):
                        (out / f'q1-mixed-bank-{filename}').write_bytes(
                            (path / filename).read_bytes())
    source_paths = [Path(__file__), HERE / 'photo_controller_path.py',
                    GATE_FITS, PHOTO_A_RECORD, PHOTO_RECORD,
                    ROM, *MAPPINGS.values(), ASSUMED / 'execute.py']
    report = dict(status='photo-candidate-ROM-feedback-not-modem-function-proof',
                  cycle_limit=CYCLES, initial_q=0, initial_ram=[0]*16,
                  gate_count=len(gates), cases=cases,
                  rom_feedback_basins=basins, zero_exit_probe=zero_exit,
                  lower_bank_probe=lower_bank_probe,
                  mixed_bank_probes=mixed_bank_probes,
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_paths},
                  limitations=[
                      'A2/A3 and I7/I0/A0/A1 connections are photo candidates, not measured nets.',
                      'The 16 ROM-enable gates fit diagnostic labels; none is physical wiring evidence.',
                      'The q3 phase fixture, branch tables, conditions, D sources and startup values are assumptions.',
                      'ALU Y and ROM feedback are not traced to a DAC, receiver input or echo path.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/photo-variant-rom-loop')
    for name in ('q1', 'q2'):
        cases = [case for case in report['cases'] if case['mapping'] == name]
        print(name, '12C periods:', sorted({case['sites']['12C']['recurrence']['period']
                                           for case in cases}, key=lambda x: -1 if x is None else x))
