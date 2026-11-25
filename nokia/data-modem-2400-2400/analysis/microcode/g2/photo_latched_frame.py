"""Hold each candidate controller frame byte at DSC D38E between latch events."""

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
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114723348.jpg'
SELECTORS = (0, 1, 64, 65)
LATCHED_FRAME = 3  # Fourth send in each preserved controller chain.
OUTPUT_VISITS = 128
CYCLES = 12 * OUTPUT_VISITS + 44


def run(out=HERE / 'results/photo-latched-frame.json'):
    controller = json.loads(CHAIN.read_text())
    if controller['distinct_chains'] != 4:
        raise ValueError('controller chain classes changed')
    _, base = fixture()
    mapping = mapping_for('b')
    cases = []
    for selector in SELECTORS:
        row = controller['rows'][selector]
        frame = [int(byte, 16)
                 for byte in row['steps'][LATCHED_FRAME]['wire'].split()]
        if row['selector'] != f'{selector:02X}' or len(frame) != 4:
            raise ValueError('controller output frame changed')
        for lane, value in enumerate(frame):
            scenario = copy.deepcopy(split_scenario(base))
            scenario['initial']['q'] = 5
            scenario['io']['read']['pc_sequences'][str(0x38E)] = [value]
            scenario['io']['read']['evidence'] += (
                '; diagnostic held byte from one hypothetical CD4094 parallel '
                'output lane; CD4094-to-D38E route and lane order untraced')
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, CYCLES, mode='integrated',
                                 out=temporary, trace_limit=CYCLES)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            inputs = [r['external_read']['value'] for r in trace if r['pc'] == 0x38E]
            outputs = [r['alu']['y'] for r in trace if r['pc'] == 0x39E]
            if (not result['clean'] or len(inputs) != OUTPUT_VISITS or
                    inputs != [value] * OUTPUT_VISITS or
                    outputs != [0xFB] + [expected(value)] * (OUTPUT_VISITS - 1)):
                raise ValueError(f'{selector:02X} lane {lane}: held-byte loop changed')
            first = next(r['cycle'] for r in trace if r['pc'] == 0x38E)
            rom = sorted({r['external_read']['address'] for r in trace
                          if r['cycle'] > first and
                          r['external_read'].get('selected_by_alu') and
                          'address' in r['external_read']})
            cases.append(dict(selector=f'{selector:02X}',
                              controller_state=row['steps'][LATCHED_FRAME]['after'],
                              latched_frame=' '.join(f'{byte:02X}' for byte in frame),
                              assumed_byte_lane=lane, held_byte=value,
                              input_visits=len(inputs), output_visits=len(outputs),
                              startup_output=outputs[0],
                              settled_output=outputs[1],
                              distinct_settled_outputs=sorted(set(outputs[1:])),
                              selected_rom_addresses_after_first_input=rom,
                              trace_digest=result['trace_digest']))
    if len(cases) != 16 or any(len(row['distinct_settled_outputs']) != 1
                               for row in cases):
        raise ValueError('latched-frame screen incomplete')
    sources = [Path(__file__), CHAIN, PHOTO,
               HERE / 'photo_shift_registers.py',
               HERE / 'split_frame_byte_rule.py',
               HERE / 'independent_slice_addresses.py',
               HERE / 'independent_slice_fields.py',
               HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
               ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='held CD4094-byte-lane hypothesis, not a transmitter',
                  fixture=dict(controller_selectors=[f'{x:02X}' for x in SELECTORS],
                               frame_number=LATCHED_FRAME + 1,
                               candidate_latch='one of four CD4094 output bytes',
                               candidate_input_pc='38E', candidate_output_pc='39E',
                               mapping=mapping['name'], initial_q=5,
                               microinstructions=CYCLES, byte_visits=OUTPUT_VISITS),
                  cases=cases,
                  result='Every held byte lane settles to a constant 39E ALU Y after startup.',
                  limitations=[
                      'The CD4094 cascade, latch strobe, byte order, parallel output route and D38E timing are untraced.',
                      'This tests one held byte at a time, not a full 32-bit simultaneous control bus.',
                      'The fourth controller frame is selected under harness-forced state expiries.',
                      '39E is an ALU value, not a traced DAC sample or line waveform.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['cases']:
        print(row['selector'], row['assumed_byte_lane'],
              f"{row['held_byte']:02X}", f"{row['settled_output']:02X}")
