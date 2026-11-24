"""Test one additional I-bit change around the bit-sensitive I1 hypothesis."""
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
from instruction_bit_neighborhood import SOURCES, after_input_groups, score_groups
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

SECOND_BITS = (2, 3, 4, 5, 6, 8)


def run(out):
    _, scenario = fixture()
    _, bits = controller_stream()
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = bits
    screened = []
    shortlist = []
    for name, path in MAPPINGS.items():
        for second_bit in SECOND_BITS:
            mapping = mapped(path)
            mapping['fields']['i']['bits'][1] = '!10.5'
            for source in SOURCES:
                for prefix in ('', '!'):
                    expression = prefix + source
                    mapping['fields']['i']['bits'][second_bit] = expression
                    result = execute(mapping, scenario, 512, mode='integrated',
                                     trace_limit=0)
                    row = dict(mapping=name, i1='!10.5', second_bit=second_bit,
                               source=expression, clean=result['clean'],
                               input_visits=result['address_counts'].get(0x38E, 0),
                               rom_reads=result['rom_reads']['selected_by_alu'],
                               output_site_visits=sum(result['address_counts'].get(pc, 0)
                                                      for pc in (0x392, 0x396, 0x39A, 0x39E)))
                    screened.append(row)
                    if row['clean'] and row['input_visits'] > 10 and row['rom_reads'] > 10:
                        shortlist.append(row)
    if len(screened) != 960:
        raise ValueError('two-bit search domain changed')

    scored = []
    witness = None
    with tempfile.TemporaryDirectory() as temporary:
        trace_path = Path(temporary)
        for candidate in shortlist:
            mapping = mapped(MAPPINGS[candidate['mapping']])
            mapping['fields']['i']['bits'][1] = '!10.5'
            mapping['fields']['i']['bits'][candidate['second_bit']] = candidate['source']
            result = execute(mapping, scenario, 512, mode='integrated',
                             out=trace_path, trace_limit=512)
            trace = [json.loads(line) for line in
                     (trace_path/'trace.jsonl').read_text().splitlines()]
            if not result['clean']:
                raise ValueError('shortlisted candidate stopped on replay')
            metrics = score_groups(after_input_groups(trace))
            preview = metrics.pop('first_8_groups')
            scored.append(dict(**candidate, **metrics,
                               trace_digest=result['trace_digest']))
            if (candidate['mapping'] == 'q1' and candidate['second_bit'] == 2 and
                    candidate['source'] == '10.0'):
                witness = dict(**scored[-1], first_8_groups=preview)
    evolving_rom = [row for row in scored if any(x > 1 for x in
                    row['rom_patterns_per_bit'].values())]
    evolving_output = [row for row in scored if any(x > 1 for x in
                       row['output_patterns_per_bit'].values())]
    sources = [Path(__file__), HERE/'instruction_bit_neighborhood.py',
               HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
               HERE/'photo_mapping_stream_screen.py', HERE/'controller_bit_dispatch.py',
               ASSUMED/'execute.py', *MAPPINGS.values()]
    report = dict(status='two-bit local mapping hypothesis, not traced wiring',
                  fixture=dict(initial_q=5, initial_ram=[0]*16,
                               input_pc='38E', controller_bits_offered=len(bits),
                               cycles=512, first_i_bit='I1=!10.5',
                               second_i_bits=list(SECOND_BITS),
                               source_lanes=list(SOURCES),
                               inversions=[False, True], mappings=list(MAPPINGS)),
                  counts=dict(variants=len(screened), clean=sum(x['clean'] for x in screened),
                              selected=len(shortlist),
                              evolving_rom=len(evolving_rom),
                              evolving_output=len(evolving_output),
                              differing_rom_patterns_between_bits=sum(
                                  x['rom_differs_between_bits'] for x in scored),
                              differing_output_sites_or_bytes_between_bits=sum(
                                  x['output_differs_between_bits'] for x in scored),
                              differing_output_bytes_between_bits=sum(
                                  x['output_byte_differs_between_bits'] for x in scored),
                              path_classes=dict(sorted(Counter(
                                  f"input={x['input_visits']};rom_gt10={x['rom_reads']>10}"
                                  for x in screened).items()))),
                  evolving_rom_candidates=evolving_rom,
                  evolving_output_candidates=evolving_output,
                  representative_bit_selected_lookup=witness,
                  shortlisted=scored,
                  limitations=['I1=!10.5 was selected because it changed a candidate output byte in the one-bit screen; no pin trace establishes it.',
                               'Only one further I bit changes at a time. Other fields, Q, RAM, ROM gate and the hypothetical D38E input remain fixed.',
                               'The tested ALU-Y output sites have no traced connection to the DAC08HP.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/second-instruction-bit-screen.json')
    print(report['counts'])
