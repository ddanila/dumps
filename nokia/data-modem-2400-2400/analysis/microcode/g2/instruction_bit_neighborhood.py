"""Search one Am2901 I-bit replacement for controller-dependent ROM evolution."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

EDIT_BITS = (1, 2, 3, 4, 5, 6, 8)
SOURCES = tuple(f'{chip}.{bit}' for chip in (10, 11) for bit in range(8))
OUTPUT_PCS = (0x392, 0x396, 0x39A, 0x39E)


def after_input_groups(trace):
    groups = []
    bit = None
    addresses = []
    outputs = []
    for row in trace:
        if row['pc'] == 0x38E:
            if bit is not None:
                groups.append(dict(bit=bit, addresses=tuple(addresses),
                                   outputs=tuple(outputs)))
            bit = row['external_read']['value']
            addresses = []
            outputs = []
            continue
        if bit is None:
            continue
        read = row.get('external_read', {})
        if read.get('selected_by_alu') and 'address' in read:
            addresses.append(read['address'])
        if row['pc'] in OUTPUT_PCS:
            outputs.append((row['pc'], row['alu']['y']))
    # The trace ends at a cycle limit, usually halfway through a symbol.
    # Only the next input read proves that the previous group is complete.
    return groups


def score_groups(groups):
    by_bit = defaultdict(lambda: dict(addresses=set(), outputs=set()))
    for group in groups[3:]:  # discard up to three startup transients
        by_bit[group['bit']]['addresses'].add(group['addresses'])
        by_bit[group['bit']]['outputs'].add(group['outputs'])
    return dict(group_count=len(groups),
                post_input_rom_reads=sum(len(group['addresses']) for group in groups),
                distinct_post_input_addresses=len({address for group in groups
                                                   for address in group['addresses']}),
                rom_patterns_per_bit={str(bit): len(by_bit[bit]['addresses'])
                                      for bit in (0, 1)},
                output_patterns_per_bit={str(bit): len(by_bit[bit]['outputs'])
                                         for bit in (0, 1)},
                rom_differs_between_bits=(bool(by_bit[0]['addresses']) and
                                          bool(by_bit[1]['addresses']) and
                                          by_bit[0]['addresses'] != by_bit[1]['addresses']),
                output_differs_between_bits=(bool(by_bit[0]['outputs']) and
                                             bool(by_bit[1]['outputs']) and
                                             by_bit[0]['outputs'] != by_bit[1]['outputs']),
                output_byte_differs_between_bits=(
                    bool(by_bit[0]['outputs']) and bool(by_bit[1]['outputs']) and
                    {value for pattern in by_bit[0]['outputs'] for _, value in pattern} !=
                    {value for pattern in by_bit[1]['outputs'] for _, value in pattern}),
                first_8_groups=[dict(bit=g['bit'], addresses=list(g['addresses']),
                                     outputs=[list(o) for o in g['outputs']])
                                for g in groups[:8]])


def run(out):
    _, scenario = fixture()
    _, bits = controller_stream()
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = bits
    total = 0
    clean = 0
    initial_candidates = []
    path_class_counts = Counter()
    for name, path in MAPPINGS.items():
        base = mapped(path)
        for bit in EDIT_BITS:
            for source in SOURCES:
                for prefix in ('', '!'):
                    total += 1
                    expression = prefix + source
                    mapping = copy.deepcopy(base)
                    mapping['fields']['i']['bits'][bit] = expression
                    result = execute(mapping, scenario, 512, mode='integrated',
                                     trace_limit=0)
                    clean += result['clean']
                    visits = result['address_counts'].get(0x38E, 0)
                    reads = result['rom_reads']['selected_by_alu']
                    path_class_counts[(visits, reads > 10)] += 1
                    if result['clean'] and visits > 10 and reads > 10:
                        initial_candidates.append(dict(mapping=name, i_bit=bit,
                                                       source=expression,
                                                       visits_38e=visits,
                                                       selected_rom_reads=reads))
    if total != 1120 or clean != total or len(initial_candidates) != 98:
        raise ValueError('one-bit neighborhood baseline changed')

    scored = []
    with tempfile.TemporaryDirectory() as temporary:
        trace_path = Path(temporary)
        for candidate in initial_candidates:
            mapping = mapped(MAPPINGS[candidate['mapping']])
            mapping['fields']['i']['bits'][candidate['i_bit']] = candidate['source']
            result = execute(mapping, scenario, 512, mode='integrated',
                             out=trace_path, trace_limit=512)
            trace = [json.loads(line) for line in
                     (trace_path/'trace.jsonl').read_text().splitlines()]
            if not result['clean']:
                raise ValueError('shortlisted candidate stopped')
            scored.append(dict(**candidate,
                               **score_groups(after_input_groups(trace)),
                               trace_digest=result['trace_digest']))

    evolving = [row for row in scored if any(value > 1 for value in
                row['rom_patterns_per_bit'].values())]
    output_evolving = [row for row in scored if any(value > 1 for value in
                       row['output_patterns_per_bit'].values())]
    sources = [Path(__file__), HERE/'photo_controller_path.py',
               HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
               HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
               *MAPPINGS.values()]
    report = dict(status='one-bit instruction-map neighborhood, not recovered wiring',
                  search=dict(mappings=list(MAPPINGS), edited_i_bits=list(EDIT_BITS),
                              source_lanes=list(SOURCES), inversion_choices=[False, True],
                              initial_q=5, zero_initial_ram=True,
                              controller_bits_offered=len(bits), cycles=512,
                              variants=total, clean=clean,
                              early_rom_and_input_candidates=len(initial_candidates),
                              path_classes={f'visits38e={visits};rom_gt10={many}': count
                                            for (visits, many), count in sorted(path_class_counts.items())}),
                  shortlisted=scored,
                  evolving_rom_candidates=[dict(mapping=x['mapping'], i_bit=x['i_bit'],
                                                source=x['source'],
                                                rom_patterns_per_bit=x['rom_patterns_per_bit'])
                                           for x in evolving],
                  evolving_output_candidates=[dict(mapping=x['mapping'], i_bit=x['i_bit'],
                                                   source=x['source'],
                                                   output_patterns_per_bit=x['output_patterns_per_bit'])
                                              for x in output_evolving],
                  limitations=['The local substitutions are hypotheses; a U10/U11 source is plausible by component placement but no individual I-bit net is traced here.',
                               'Only one I bit changes at a time; multi-bit layouts and other PROM lanes are not excluded.',
                               'The same Q=5, ROM-enable, branch, condition and hypothetical D38E controller route are reused for every candidate.',
                               'Groups are counted only when closed by the next D38E read; the final partial group is discarded.',
                               'ROM activity and candidate ALU-Y outputs are diagnostics, not line-output proof.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/instruction-bit-neighborhood.json')
    print(report['search']['variants'],
          len(report['evolving_rom_candidates']),
          len(report['evolving_output_candidates']))
