"""Run every fitted ROM gate that selects word 299 in the photo-compatible mapping."""
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
from common import read, save
from execute import execute


def run(out, cycles=2048):
    if cycles < 128:
        raise ValueError('cycle limit must cover the candidate drain')
    config_path = ASSUMED / 'gate-runtime-study.json'
    config = read(config_path)
    base_path = ASSUMED / config['scenario']
    graph_path = ASSUMED / config['static_scenario']
    mapping_path = ASSUMED / 'results/selector-completion/swapped-marked/mapping.json'
    gate_path = ASSUMED / 'results/rom-gate-study/report.json'
    sine_path = ASSUMED / 'sine-operand-study.json'
    base = read(base_path)
    graph = read(graph_path)
    base['branch_tables'] = graph['branch_tables']
    base['dispatch']['tables'] = graph['dispatch']['tables']
    base['initial'] = dict(pc=0, ram=[0]*16, q=0)
    base['dispatch']['value'] = 1
    base['condition']['brt_unconditional_gate'] = config['gate']
    base['io']['read'] = dict(mode='pc_sequence', value=255, table=[0],
        pc_sequences={str(pc): [255, 0] for pc in (0x117, 0x106)},
        sequence_end='hold-last', status='stub',
        evidence='Diagnostic early replies from gate-runtime-study; not controller data.')
    mapping = read(mapping_path)
    fits = [fit for fit in read(gate_path)['fits'] if 0x299 in fit['pcs']]
    fits.sort(key=lambda fit: (len(fit['pcs']), fit['terms']))
    rom_hash = read(sine_path)['rom_sha256']
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for fit in fits:
            scenario = copy.deepcopy(base)
            scenario['name'] = f'photo-compatible fitted swap, D=FF startup, gate {fit["terms"]}'
            scenario['io']['read']['expected_sha256'] = rom_hash
            scenario['io']['read']['address'] = dict(source='previous_y', bank=256,
                initial_y=0, pcs=fit['pcs'], status='hypothesis',
                evidence='Three-term diagnostic ROM gate; physical enable and address wiring unverified.')
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=path, trace_limit=cycles)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
            drain = [row for row in trace if row['pc'] == 0x299]
            reads = [dict(cycle=row['cycle'], address=row['external_read']['address'],
                          value=row['external_read']['value'], q=row['q'], y=row['alu']['y'])
                     for row in drain if row.get('external_read', {}).get('selected_by_alu')]
            count_299 = result['address_counts'].get(0x299, 0)
            case = dict(terms=fit['terms'], gate_pc_count=len(fit['pcs']),
                        clean=result['clean'], final_pc=f'{result["final_state"]["pc"]:03X}',
                        visits_299=count_299, selected_reads_299=reads,
                        visits_output_392=result['address_counts'].get(0x392, 0),
                        trace_digest=result['trace_digest'],
                        mapping_digest=result['mapping_digest'],
                        scenario_digest=result['scenario_digest'],
                        am27s31_hash=result['am27s31_hash'])
            if count_299 != len(reads):
                raise ValueError(f'299 visits/read mismatch: {count_299}/{len(reads)} for {fit["terms"]}')
            cases.append(case)
            if fit == fits[0]:
                (out / 'witness-trace.jsonl').write_bytes((path / 'trace.jsonl').read_bytes())
                (out / 'witness-scenario.json').write_bytes((path / 'scenario.json').read_bytes())
                save(out / 'witness-mapping.json', mapping)
    source_paths = [Path(__file__), config_path, base_path, graph_path,
                    mapping_path, gate_path, sine_path,
                    ASSUMED / 'execute.py', ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='fitted-ROM-drain-not-G2-C2', cycle_limit=cycles,
                  candidate_gate_count=len(fits), cases=cases,
                  visit_distribution=dict(Counter(case['visits_299'] for case in cases)),
                  source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source_paths},
                  limitations=['The ROM gates and branch condition are diagnostic fits, not traced wiring.',
                               'D=FF startup replies and dispatch index 1 are supplied by the scenario.',
                               'No controller bitstream, DAC bus or receive/echo path is connected.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/fitted-rom-drain')
    print(report['candidate_gate_count'], 'gates;', report['visit_distribution'],
          'visits at 299; output 392 in',
          sum(bool(c['visits_output_392']) for c in report['cases']), 'cases')
