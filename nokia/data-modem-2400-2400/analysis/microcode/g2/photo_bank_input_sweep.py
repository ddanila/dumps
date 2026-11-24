"""Screen the early D byte against both candidate 12C ROM banks in q1."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path.insert(0, str(ASSUMED))
from common import read, save
from execute import execute

MAPPING = HERE / 'results/photo-variant-rom-loop/q1-witness-mapping.json'
SCENARIO = HERE / 'results/photo-variant-rom-loop/q1-mixed-bank-scenario.json'
ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
CYCLES = 256


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    mapping = read(MAPPING)
    base = read(SCENARIO)
    cases = []
    for bank_12c in (0, 256):
        final_pcs = Counter()
        first_12c = Counter()
        phase_map_inputs = []
        output_site_inputs = []
        final_states = set()
        trace_digests = set()
        clean_count = 0
        for value in range(256):
            scenario = copy.deepcopy(base)
            scenario['name'] += f'; diagnostic D002={value:02X}, A8(12C)={bank_12c}'
            scenario['io']['read']['pc_sequences']['2'] = [value]
            scenario['io']['read']['address']['bank_by_pc']['300'] = bank_12c
            result = execute(mapping, scenario, CYCLES, mode='integrated', trace_limit=0)
            clean_count += result['clean']
            final_pcs[f'{result["final_state"]["pc"]:03X}'] += 1
            first_12c[result['address_counts'].get(0x12C, 0)] += 1
            final_states.add(json.dumps((result['final_state']['q'],
                                         result['final_state']['ram'])))
            trace_digests.add(result['trace_digest'])
            if any(0x07C <= address <= 0x07F
                   for address in result['rom_reads']['address_counts']):
                phase_map_inputs.append(value)
            if any(0x390 <= pc <= 0x39F for pc in result['visited']):
                output_site_inputs.append(value)
        cases.append(dict(bank_12c=bank_12c, clean_count=clean_count,
                          final_pcs=dict(final_pcs), visits_12c=dict(first_12c),
                          distinct_final_ram_q=len(final_states),
                          distinct_trace_digests=len(trace_digests),
                          phase_map_inputs=phase_map_inputs,
                          candidate_output_site_inputs=output_site_inputs))
    witnesses = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for value in (0, 165, 255):
            scenario = copy.deepcopy(base)
            scenario['io']['read']['pc_sequences']['2'] = [value]
            result = execute(mapping, scenario, 128, mode='integrated',
                             out=path, trace_limit=128)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
            row = next(row for row in trace if row['pc'] == 2)
            witnesses.append(dict(input=value, external_read=row['external_read'],
                                  alu=row['alu'], final_pc=f'{result["final_state"]["pc"]:03X}',
                                  trace_digest=result['trace_digest']))
    report = dict(status='diagnostic-input-screen-not-modem-function-proof',
                  cycle_limit=CYCLES, input_pc='002', input_values=list(range(256)),
                  cases=cases, witnesses=witnesses,
                  source_sha256={str(p.relative_to(HERE.parents[2])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (MAPPING, SCENARIO, ROM, ASSUMED / 'execute.py',
                                           Path(__file__))},
                  limitations=[
                      'PC 002 is a D-consuming site in this candidate map; its physical source is unknown.',
                      'The diagnostic ROM gate, A8 choice, flag policy and startup state are assumptions.',
                      'The 392-39F words are candidate output sites, not traced DAC writes.',
                      'A256-cycle scope and this one mapping do not rule out other paths or an external restart.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/photo-bank-input-sweep')
    print([(case['bank_12c'], case['final_pcs']) for case in report['cases']])
