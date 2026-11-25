"""Replay executed 8031 receive/state frames into the split-slice DSC candidate."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from photo_mapping_stream_screen import MAPPINGS
from split_frame_byte_rule import expected
from split_slice_probe import split_scenario

CHAIN = HERE / 'results/received-chain.json'
SELECTORS = (0, 1, 64, 65)
REPEATS = 8


def run(out=HERE / 'results/received-chain-microcode.json'):
    chain = json.loads(CHAIN.read_text())
    if chain['status'] != '256 preserved-image USART-receive/state/send chains pass':
        raise ValueError('received-chain source changed')
    _, base = fixture()
    mapping = mapping_for('b')
    cases = []
    output_by_selector = {}
    for selector in SELECTORS:
        row = chain['rows'][selector]
        if row['selector'] != f'{selector:02X}':
            raise ValueError('received-chain row order changed')
        frame = [int(byte, 16) for step in row['steps']
                 for byte in step['wire'].split()]
        if len(frame) != 16:
            raise ValueError('expected four four-byte frames')
        values = frame * REPEATS
        scenario = copy.deepcopy(split_scenario(base))
        scenario['initial']['q'] = 5
        scenario['io']['read']['pc_sequences'][str(0x38E)] = values
        cycles = 12 * len(values) + 44
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        inputs = [row['external_read']['value'] for row in trace
                  if row['pc'] == 0x38E]
        outputs = [row['alu']['y'] for row in trace if row['pc'] == 0x39E]
        predicted = [0xFB] + [expected(value) for value in values[:-1]]
        if not result['clean'] or inputs != values or outputs != predicted:
            raise ValueError(f'selector {selector:02X}: bridge loop or byte rule changed')
        first_input_cycle = next(row['cycle'] for row in trace if row['pc'] == 0x38E)
        selected_rom = sorted({row['external_read']['address'] for row in trace
                               if row['cycle'] > first_input_cycle and
                               row['external_read'].get('selected_by_alu') and
                               'address' in row['external_read']})
        output_by_selector[selector] = outputs
        cases.append(dict(selector=f'{selector:02X}',
                          state_chain=[step['after'] for step in row['steps']],
                          four_frames=[step['wire'] for step in row['steps']],
                          input_bytes=len(inputs), output_visits=len(outputs),
                          first_17_outputs=outputs[:17],
                          distinct_output_bytes=sorted(set(outputs)),
                          selected_rom_addresses_after_first_input=selected_rom,
                          final_pc=f'{result["final_state"]["pc"]:03X}',
                          trace_digest=result['trace_digest']))
    pairs = {}
    for a, b in ((0, 1), (0, 64), (1, 65), (64, 65)):
        positions = [i for i, (x, y) in enumerate(zip(output_by_selector[a],
                                                       output_by_selector[b]))
                     if x != y]
        if not positions:
            raise ValueError(f'controller selectors {a}/{b} indistinguishable')
        pairs[f'{a:02X}/{b:02X}'] = dict(differing_output_visits=len(positions),
                                        first_16_positions=positions[:16],
                                        differing_sites_mod_16=sorted({i % 16
                                                                       for i in positions}))
    sources = [Path(__file__), CHAIN, HERE / 'received_chain.py',
               HERE / 'split_frame_byte_rule.py',
               HERE / 'independent_slice_addresses.py',
               HERE / 'independent_slice_fields.py',
               HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
               ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='conditional 8031-receive-to-DSC-byte-relay bridge',
                  fixture=dict(received_selector_classes=[f'{x:02X}' for x in SELECTORS],
                               controller_frames_per_class=4,
                               repeated_frame_cycles=REPEATS,
                               candidate_input_pc='38E', candidate_output_pc='39E',
                               mapping=mapping['name'], initial_q=5),
                  cases=cases, pairwise_output_differences=pairs,
                  interpretation='The executed controller receive byte changes the state frames; replaying those frames through one assumed DSC D-input changes the reached 39E ALU byte by the already-derived field-extraction rule.',
                  limitations=[
                      'The controller-to-DSC byte route and timing are untraced and the frame repetition is diagnostic.',
                      'The 39E ALU byte is not a traced DAC sample or recovered modem command.',
                      'The ROM is read at a fixed address in this fixture; no carrier phase or receiver operation is shown.',
                      'Controller state handoffs and timer expiries are synthetic, though its ROM runs unchanged.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(row['selector'], row['selected_rom_addresses_after_first_input'])
           for row in report['cases']])
    print(report['pairwise_output_differences'])
