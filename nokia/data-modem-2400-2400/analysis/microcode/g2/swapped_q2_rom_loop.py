"""Execute q2 photo-swapped under every diagnostic ROM gate selecting 127."""
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
from sine_operand_study import scenario_for_phase
from photo_b_constraints import swapped


def run(out, cycles=512):
    if cycles < 64:
        raise ValueError('cycle limit must repeat the 127 loop')
    config_path = ASSUMED / 'sine-operand-study.json'
    mapping_path = ASSUMED / 'results/independent-study/variant-2.json'
    gate_path = ASSUMED / 'results/rom-gate-study/report.json'
    config = read(config_path)
    mapping = swapped(read(mapping_path))
    gates = [fit for fit in read(gate_path)['fits'] if 0x127 in fit['pcs']]
    gates.sort(key=lambda fit: (len(fit['pcs']), fit['terms']))
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for gate in gates:
            scenario = scenario_for_phase(config, 'q3', 32)
            scenario['name'] = f'q2 photo A/B swap; ROM gate {gate["terms"]}; fixture phase 32'
            scenario['io']['read']['address']['pcs'] = gate['pcs']
            result = execute(mapping, scenario, cycles, mode='integrated', out=path, trace_limit=cycles)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
            rows = [row for row in trace if row['pc'] == 0x127]
            reads = [row for row in rows if row.get('external_read', {}).get('selected_by_alu')]
            case = dict(terms=gate['terms'], selected_pcs=len(gate['pcs']),
                        clean=result['clean'], final_pc=f'{result["final_state"]["pc"]:03X}',
                        visits_127=len(rows), selected_reads_127=len(reads),
                        addresses_127=sorted({row['external_read']['address'] for row in reads}),
                        values_127=sorted({row['external_read']['value'] for row in reads}),
                        y_127=sorted({row['alu']['y'] for row in rows}),
                        q_127=sorted({row['q'] for row in rows}),
                        last_16_y=[row['alu']['y'] for row in rows[-16:]],
                        trace_digest=result['trace_digest'],
                        mapping_digest=result['mapping_digest'],
                        scenario_digest=result['scenario_digest'],
                        am27s31_hash=result['am27s31_hash'])
            cases.append(case)
            if gate == gates[0]:
                (out / 'witness-trace.jsonl').write_bytes((path / 'trace.jsonl').read_bytes())
                save(out / 'witness-mapping.json', mapping)
                (out / 'witness-scenario.json').write_bytes((path / 'scenario.json').read_bytes())
    sources = [Path(__file__), config_path, mapping_path, gate_path,
               HERE / 'photo-b-constraints.json', HERE / 'photo_b_constraints.py',
               ASSUMED / 'sine_operand_study.py', ASSUMED / 'execute.py',
               ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='candidate-ROM-loop-not-G2-C2', cycle_limit=cycles,
                  fixture_phase=32, candidate_gate_count=len(gates), cases=cases,
                  source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sources},
                  limitations=['The gates fit diagnostic labels, not measured ROM enable wiring.',
                               'The phase-32 fixture and other external inputs are scenario supplied.',
                               'The 127 loop has no traced DAC output or controller bitstream.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/swapped-q2-rom-loop')
    print('gates:', report['candidate_gate_count'])
    print('visits/read/stable tail:', [(c['visits_127'], c['selected_reads_127'],
          len(set(c['last_16_y']))) for c in report['cases']])
