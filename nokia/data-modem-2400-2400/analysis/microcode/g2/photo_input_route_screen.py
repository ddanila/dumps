"""Screen controller frames and ADC samples at hypothetical D38E across mappings."""
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
from adc_sample_path import DIBITS
from controller_bit_dispatch import groups_for, post_group_states
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import receive, transmit

CONTROLLER = HERE / 'results/main-loop-serial.json'
SELECTORS = ('00', '20', '40', '60')


def execute_stream(mapping, base, values):
    scenario = copy.deepcopy(base)
    scenario['io']['read']['pc_sequences']['910'] = values
    cycles = 12 * len(values) + 44
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    reads = [row['external_read']['value'] for row in trace if row['pc'] == 0x38E]
    groups = groups_for(trace)
    states = post_group_states(trace, scenario['initial']['ram'])
    if not result['clean'] or reads != values or len(groups) != len(values) or len(states) != len(values):
        raise ValueError('candidate D38E stream did not complete one group per byte')
    by_input = defaultdict(set)
    for value, group, state in zip(values, groups, states):
        by_input[value].add(json.dumps(dict(index=group['index'],
                                            output=group['bytes'], state=state),
                                       sort_keys=True))
    first_input = next(row['cycle'] for row in trace if row['pc'] == 0x38E)
    post_rom = [row for row in trace if row['cycle'] > first_input and
                row.get('external_read', {}).get('selected_by_alu') and
                'address' in row['external_read']]
    candidate_y = {f'{pc:03X}': sorted({row['alu']['y'] for row in trace
                                       if row['pc'] == pc})
                   for pc in (0x392, 0x396, 0x39A, 0x39E)}
    return dict(clean=True, input_bytes=len(values), distinct_input_bytes=len(by_input),
                max_signatures_per_input=max(map(len, by_input.values())),
                post_input_rom_reads=len(post_rom),
                candidate_y=candidate_y,
                final_pc=f"{result['final_state']['pc']:03X}",
                trace_digest=result['trace_digest']), by_input


def run(out):
    controller = json.loads(CONTROLLER.read_text())
    if len(controller['rows']) != 256 or controller['distinct_streams'] != 4:
        raise ValueError('controller frame report changed')
    frame_rows = {row['selector']: row for row in controller['rows']}
    frame_streams = {selector: [int(byte, 16) for frame in frame_rows[selector]['frames']
                                for byte in frame.split()]
                     for selector in SELECTORS}
    if any(len(values) != 48 for values in frame_streams.values()):
        raise ValueError('expected 12 four-byte controller frames')
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference PCM did not recover its dibits')
    adc_forward = [127 - sample for sample in pcm]
    adc_reverse = adc_forward[::-1]
    _, base = fixture()
    base['initial']['q'] = 5

    cases = []
    for name, path in MAPPINGS.items():
        mapping = mapped(path)
        forward, forward_map = execute_stream(mapping, base, adc_forward)
        reverse, reverse_map = execute_stream(mapping, base, adc_reverse)
        if forward_map != reverse_map or forward['max_signatures_per_input'] != 1:
            raise ValueError(f'{name}: candidate ADC path gained history')
        cases.append(dict(mapping=name, stimulus='ADC complementary forward', **forward))
        cases.append(dict(mapping=name, stimulus='ADC complementary reverse', **reverse))
        for selector, values in frame_streams.items():
            row, _ = execute_stream(mapping, base, values)
            cases.append(dict(mapping=name, stimulus=f'controller frames selector {selector}',
                              **row))
    if len(cases) != 30 or any(row['post_input_rom_reads'] for row in cases):
        raise ValueError('post-input ROM behavior changed')

    sources = [Path(__file__), CONTROLLER, HERE/'adc_sample_path.py',
               HERE/'reference_modem.py', HERE/'photo_controller_path.py',
               HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
               HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
               *MAPPINGS.values()]
    report = dict(status='scoped D38E input-route screen, not board wiring',
                  fixture=dict(mapping_count=len(MAPPINGS), initial_q=5,
                               initial_ram=[0]*16, candidate_input_pc='38E',
                               controller_selectors=list(SELECTORS),
                               frame_bytes_per_selector=48,
                               adc_samples=len(adc_forward),
                               adc_coding='127 - reference signed PCM'),
                  cases=cases,
                  interpretation='All five mappings consume each stream. The ADC candidate has one post-group signature per input byte, invariant to stream reversal. None of the 30 runs reads the Am27S31 after the first D38E input.',
                  limitations=['The frame and ADC bytes are separate alternative stimuli at D38E, an untraced connection.',
                               'The same q3-derived branch, ROM gate, initial state and sample/command timing are used for all five mappings.',
                               'Other input PCs, latch phases, simultaneous controller state and ADC traffic, and physical output routes are not tested.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-input-route-screen.json')
    print([(case['mapping'], case['stimulus'], case['max_signatures_per_input'],
            case['post_input_rom_reads']) for case in report['cases']])
