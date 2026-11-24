"""Screen the fitted-original reset wrapper with diagnostic Am27S31 gates."""

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

MAPPING = ASSUMED / 'results/defined-condition-fit/reset-original_previous-zero/mapping.json'
SCENARIO = ASSUMED / 'results/polling-study/immediate-one/scenario.json'
GATES = ASSUMED / 'results/rom-gate-study/report.json'
SINE = ASSUMED / 'sine-operand-study.json'
MAIN_GATE_INDEX = 61
SAMPLE_BYTES = (0, 1, 64, 128, 255)


def fixture(source, gate, rom_hash, bank, value):
    scenario = copy.deepcopy(source)
    scenario['name'] = 'fitted-original reset, diagnostic ROM shift wrapper'
    scenario['dispatch']['mode'] = 'random'
    scenario['initial'] = dict(pc=0, ram=[0] * 16, q=0)
    scenario['io']['read'] = dict(
        mode='pc_sequence', value=value, table=[0], pc_sequences={},
        sequence_end='hold-last', status='stub', expected_sha256=rom_hash,
        evidence='Constant diagnostic external D; not the controller protocol.',
        address=dict(source='previous_y', bank=bank, initial_y=0,
                     pcs=gate['pcs'], status='hypothesis',
                     evidence='Three-term ROM-read gate fit; physical gate and address bus untraced.'))
    return scenario


def outcome(result):
    counts = result['address_counts']
    return dict(clean=result['clean'], final_pc=f"{result['final_state']['pc']:03X}",
                visits_299=counts.get(0x299, 0), visits_187=counts.get(0x187, 0),
                visits_24e=counts.get(0x24e, 0), visits_084=counts.get(0x084, 0),
                visits_output_392=counts.get(0x392, 0))


def run(out, full=True):
    mapping = read(MAPPING)
    source = read(SCENARIO)
    fits = read(GATES)['fits']
    rom_hash = read(SINE)['rom_sha256']
    selected = [(i, fit) for i, fit in enumerate(fits) if 0x187 in fit['pcs']]
    if len(selected) != 12 or MAIN_GATE_INDEX not in [i for i, _ in selected]:
        raise ValueError('ROM gate fit set changed; review the experiment')
    main_gate = fits[MAIN_GATE_INDEX]
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    gate_cases = []
    value_range = range(256) if full else SAMPLE_BYTES
    for seed in (6, 14):
        for bank in (0, 256):
            outcomes = Counter()
            min_299, max_299 = 1001, 0
            failures = []
            output_hits = 0
            for value in value_range:
                scenario = fixture(source, main_gate, rom_hash, bank, value)
                result = execute(mapping, scenario, 1000, seed=seed,
                                 mode='integrated', trace_limit=0)
                case = outcome(result)
                key = (case['clean'], case['final_pc'], case['visits_187'] > 0,
                       case['visits_24e'] > 0, case['visits_084'] > 0)
                outcomes[str(key)] += 1
                output_hits += case['visits_output_392'] > 0
                min_299 = min(min_299, case['visits_299'])
                max_299 = max(max_299, case['visits_299'])
                if key != (True, '084', True, True, True):
                    failures.append(dict(value=value, **case))
            cases.append(dict(seed=seed, bank=bank, values=len(value_range),
                              outcomes=dict(outcomes), visits_299_range=[min_299, max_299],
                              output_hit_cases=output_hits, exceptions=failures))
    for index, fit in selected:
        by_bank = {}
        for bank in (0, 256):
            by_bank[str(bank)] = []
            for value in SAMPLE_BYTES:
                result = execute(mapping, fixture(source, fit, rom_hash, bank, value),
                                 1000, seed=6, mode='integrated', trace_limit=0)
                by_bank[str(bank)].append(dict(value=value, **outcome(result)))
        gate_cases.append(dict(index=index, terms=fit['terms'], selected_pcs=len(fit['pcs']),
                               banks=by_bank))
    with tempfile.TemporaryDirectory() as temporary:
        scenario = fixture(source, main_gate, rom_hash, 256, 128)
        result = execute(mapping, scenario, 1000, seed=6, mode='integrated',
                         out=Path(temporary), trace_limit=300)
        trace = [json.loads(line) for line in (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        reads = {}
        for pc in (0x299, 0x187):
            reads[f'{pc:03X}'] = [dict(cycle=row['cycle'], q=row['q'],
                                      address=row['external_read'].get('address'),
                                      value=row['external_read']['value'], y=row['alu']['y'])
                                 for row in trace if row['pc'] == pc]
        (out / 'witness-trace.jsonl').write_bytes((Path(temporary) / 'trace.jsonl').read_bytes())
        (out / 'witness-scenario.json').write_bytes((Path(temporary) / 'scenario.json').read_bytes())
    report = dict(status='diagnostic-wrapper-exit-not-G2-C2-or-C3',
                  mapping='fitted-original/reset-original_previous-zero',
                  main_gate_index=MAIN_GATE_INDEX, main_gate_terms=main_gate['terms'],
                  main_gate_pc_count=len(main_gate['pcs']),
                  cycle_limit=1000, full_sweep=full, cases=cases,
                  alternative_gate_cases=gate_cases,
                  witness=dict(seed=6, bank=256, value=128, outcome=outcome(result), reads=reads),
                  limitations=['ROM gate and previous-Y address feedback are hypotheses, not traced nets.',
                               'Dispatch is seeded random and D is a constant stub, not 8031 commands or bits.',
                               '084 is a wait loop; no line output or receiver/echo function is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), MAPPING, SCENARIO, GATES, SINE,
                                              ASSUMED / 'execute.py', HERE.parent / 'model.py')})
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/rom-shift-wrapper')
    print('Full sweep:', sum(c['values'] for c in report['cases']), 'cases;',
          'alternative gate cases:', len(report['alternative_gate_cases']) * 10)
