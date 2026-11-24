"""Run the photo-compatible q3 swap through the fitted ROM gate and output loop."""
import argparse
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

OUTPUT = tuple(range(0x392, 0x396))
GATE = [['11.4', 0], ['18.5', 0]]


def run_case(mapping, config, gate, phase, cycles, trace_path, zero_317=False):
    scenario = scenario_for_phase(config, 'q3', phase)
    scenario['name'] = f'q3 photo A/B swap, gate {gate["terms"]}, quarter-sine phase {phase}'
    scenario['io']['read']['address']['pcs'] = [pc for pc in gate['pcs'] if not (zero_317 and pc == 0x317)]
    if zero_317:
        scenario['name'] += '; zero D at 317'
        scenario['io']['read']['pc_sequences'][str(0x317)] = [0]
    scenario['io']['read']['address']['evidence'] = (
        'The global two-bit gate from rom-gate-study is fitted to diagnostic labels, '
        'not physically measured. This run uses the photo-compatible A/B swap.')
    result = execute(mapping, scenario, cycles, mode='integrated',
                     out=trace_path, trace_limit=cycles)
    trace = [json.loads(line) for line in (trace_path / 'trace.jsonl').read_text().splitlines()]
    reads = [dict(cycle=row['cycle'], pc=f'{row["pc"]:03X}',
                  address=f'{row["external_read"]["address"]:03X}',
                  value=row['external_read']['value'])
             for row in trace if 'address' in row.get('external_read', {})
             and row['external_read']['selected_by_alu']]
    output = [row for row in trace if row['pc'] in OUTPUT]
    groups = [output[i:i+4] for i in range(0, len(output), 4)]
    complete = [group for group in groups if [r['pc'] for r in group] == list(OUTPUT)
                and [r['cycle'] for r in group] == list(range(group[0]['cycle'], group[0]['cycle']+4))]
    samples = [tuple(row['alu']['y'] for row in group) for group in complete]
    cycles_at_first_output = [group[0]['cycle'] for group in complete]
    state = dict(phase=phase, clean=result['clean'], final_pc=f'{result["final_state"]["pc"]:03X}',
                 completed_cycles=result['completed_cycles'], rom_reads=reads,
                 mapping_digest=result['mapping_digest'], scenario_digest=result['scenario_digest'],
                 rom_hashes=result['rom_hashes'], am27s31_hash=result['am27s31_hash'],
                 complete_output_groups=len(complete), first_output_cycle=cycles_at_first_output[0] if complete else None,
                 output_group_periods=sorted(set(b-a for a,b in zip(cycles_at_first_output,cycles_at_first_output[1:]))),
                 distinct_output_groups=len(set(samples)), first_output_group=list(samples[0]) if samples else None,
                 first_q=complete[0][0]['q'] if complete else None,
                 distinct_q_at_output=len({group[0]['q'] for group in complete}),
                 trace_digest=result['trace_digest'])
    return state


def run(out, cycles=1024):
    if cycles < 128:
        raise ValueError('cycle limit must reach and repeat the candidate output loop')
    config_path = ASSUMED / 'sine-operand-study.json'
    config = read(config_path)
    mapping_path = ASSUMED / 'results/independent-study/variant-3.json'
    mapping = swapped(read(mapping_path))
    gate_path = ASSUMED / 'results/rom-gate-study/report.json'
    gate = next(fit for fit in read(gate_path)['fits'] if fit['terms'] == GATE)
    out.mkdir(parents=True, exist_ok=True)
    outcomes = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for phase in range(65):
            case = run_case(mapping, config, gate, phase, cycles, path)
            outcomes.append(case)
            if phase in (0, 32, 64):
                save(out / f'phase-{phase:02x}.json', case)
                if phase == 32:
                    (out / 'phase-20-trace.jsonl').write_bytes((path / 'trace.jsonl').read_bytes())
                    save(out / 'phase-20-mapping.json', mapping)
                    # The executor saved the exact scenario used for this witness.
                    (out / 'phase-20-scenario.json').write_bytes((path / 'scenario.json').read_bytes())
        control = run_case(mapping, config, gate, 32, cycles, path, zero_317=True)
        save(out / 'phase-20-zero-317.json', control)
        (out / 'phase-20-zero-317-trace.jsonl').write_bytes((path / 'trace.jsonl').read_bytes())
        (out / 'phase-20-zero-317-scenario.json').write_bytes((path / 'scenario.json').read_bytes())
    source_paths = [Path(__file__), config_path, mapping_path, gate_path,
                    HERE / 'photo-b-constraints.json', ASSUMED / 'sine_operand_study.py',
                    HERE / 'photo_b_constraints.py', ASSUMED / 'execute.py',
                    ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='candidate-loop-execution-not-G2-C2',
                  cycle_limit=cycles, gate_terms=GATE,
                  tested_phases=list(range(65)), outcomes=outcomes,
                  zero_317_control=control,
                  repeated_phases=[row['phase'] for row in outcomes if row['complete_output_groups']>1],
                  changing_output_phases=[row['phase'] for row in outcomes if row['distinct_output_groups']>1],
                  source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source_paths},
                  interpretation='The global diagnostic ROM gate plus photo-compatible q3 A/B swap can feed a quarter-sine byte into the paired-output routine. The study tests whether that output evolves during a single run rather than only between different reset fixtures.',
                  limitations=['The gate was fitted to diagnostic labels, not physical enable pins.',
                               'The scenario supplies phase at 316; phase variation across separate runs is external stimulus.',
                               'The branch, condition, D routing and clock schedule are still hypotheses.',
                               'ALU Y at 392-395 is a candidate output quartet, not a traced DAC bus.',
                               'There is no controller-driven bitstream or receive/echo path in this test.'])
    save(out / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'results/swapped-sine-loop')
    parser.add_argument('--cycles', type=int, default=1024)
    args = parser.parse_args()
    report = run(args.out, args.cycles)
    print('repeated phases:', len(report['repeated_phases']),
          'changing output phases:', len(report['changing_output_phases']))
    for phase in (0, 32, 64):
        row=report['outcomes'][phase]
        print(phase, row['final_pc'], row['complete_output_groups'],
              row['first_output_group'], row['output_group_periods'])


if __name__ == '__main__':
    main()
