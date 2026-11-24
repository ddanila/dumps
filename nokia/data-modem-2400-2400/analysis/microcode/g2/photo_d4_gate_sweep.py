"""Vary the diagnostic ROM-read gate around the photo-derived U10 D4 lead."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent/'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from instruction_bit_neighborhood import after_input_groups, score_groups
from photo_controller_path import fixture, GATE_FITS
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_u10_d4_probe import visible_segment


def run(out):
    segment = visible_segment()
    fits = json.loads(GATE_FITS.read_text())['fits']
    _, base = fixture()
    _, bits = controller_stream()
    base['initial']['q'] = 5
    base['io']['read']['pc_sequences']['910'] = bits
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        trace_path = Path(temporary)
        for name in ('q1', 'fitted_swapped'):
            for source in ('10.4', '!10.4'):
                mapping = mapped(MAPPINGS[name])
                mapping['fields']['i']['bits'][1] = source
                for gate_index, gate in enumerate(fits):
                    scenario = copy.deepcopy(base)
                    scenario['io']['read']['address']['pcs'] = gate['pcs']
                    result = execute(mapping, scenario, 512, mode='integrated',
                                     out=trace_path, trace_limit=512)
                    trace = [json.loads(line) for line in
                             (trace_path/'trace.jsonl').read_text().splitlines()]
                    metrics = score_groups(after_input_groups(trace))
                    metrics.pop('first_8_groups')
                    cases.append(dict(mapping=name, hypothetical_i1_source=source,
                                      gate_index=gate_index, gate_terms=gate['terms'],
                                      clean=result['clean'],
                                      input_visits=result['address_counts'].get(0x38E, 0),
                                      selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                      trace_digest=result['trace_digest'], **metrics))
    if len(fits) != 137 or len(cases) != 548:
        raise ValueError('diagnostic gate domain changed')
    classes = Counter((row['mapping'], row['hypothetical_i1_source'],
                       row['selected_rom_reads'] > 10,
                       max(row['rom_patterns_per_bit'].values()),
                       max(row['output_patterns_per_bit'].values())) for row in cases)
    evolving = [row for row in cases if any(n > 1 for n in
                (*row['rom_patterns_per_bit'].values(),
                 *row['output_patterns_per_bit'].values()))]
    paths = [Path(__file__), HERE/'photo_u10_d4_probe.py', GATE_FITS,
             HERE/'instruction_bit_neighborhood.py', HERE/'photo_controller_path.py',
             HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
             HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
             MAPPINGS['q1'], MAPPINGS['fitted_swapped']]
    report = dict(status='counterfactual I1 source plus diagnostic gate sweep, not board wiring',
                  visible_segment=segment,
                  fixture=dict(initial_q=5, initial_ram=[0]*16,
                               hypothetical_input_pc='38E', controller_bits_offered=len(bits),
                               cycles=512, mappings=['q1', 'fitted_swapped'],
                               hypothetical_i1_sources=['10.4', '!10.4'],
                               gate_fits=len(fits)),
                  counts=dict(cases=len(cases), clean=sum(row['clean'] for row in cases),
                              evolving=len(evolving),
                              classes=[dict(mapping=k[0], hypothetical_i1_source=k[1],
                                            many_rom_reads=k[2],
                                            max_rom_patterns_per_bit=k[3],
                                            max_output_patterns_per_bit=k[4], cases=v)
                                       for k,v in sorted(classes.items())]),
                  evolving_cases=evolving, cases=cases,
                  limitations=['The photo fragment approaches U5 Q3, an output, not its D3 input. PROM/latch output enables and any route to Am2901 I1 are untraced.',
                               'The I1=10.4/!10.4 substitution does not model bus contention or latch timing.',
                               'The 137 ROM gates are diagnostic fits, not a complete set of physical enable circuits.',
                               'Other fields, initial states, input paths and DAC capture remain hypothetical.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-d4-gate-sweep.json')
    print(report['counts'])
