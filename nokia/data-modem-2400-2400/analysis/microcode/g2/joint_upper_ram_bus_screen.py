"""Screen fixed receive-loop PROM outputs for direct external-RAM controls."""

import hashlib
import json
import random
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

VISITS = 2048
CYCLES = 8 * VISITS + 47
LOOP = (0x3EA, 0x3EB, 0x3EC, 0x3F7,
        0x3F8, 0x3F9, 0x3FA, 0x3ED)
CHIPS = ('U10', 'U11', 'U17', 'U18')
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114811760.jpg'


def capture(mapping, base, offered):
    scenario = scenario_for_full_byte(base, offered, 'complementary')
    raw = {}
    outputs = defaultdict(list)
    started = False
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if row['pc'] == LOOP[0]:
                started = True
            if not started:
                continue
            pc = row['pc']
            if pc not in LOOP:
                raise ValueError(('fixed receive loop left', pc))
            word = tuple(row['raw'])
            if pc in raw and raw[pc] != word:
                raise ValueError(('PROM word changed at same address', pc))
            raw[pc] = word
            outputs[pc].append(row['alu']['y'])
            if pc == 0x3F8:
                read = row['external_read']
                if (not read.get('selected_by_alu') or
                        read['value'] != offered[len(outputs[pc]) - 1]):
                    raise ValueError('ADC byte was not selected')
    if (not result['clean'] or
            result['read_sequence_visits'].get(0x3F8) != VISITS or
            set(raw) != set(LOOP)):
        raise ValueError('fixed receive loop did not sustain')
    return raw, outputs, result['trace_digest']


def sites(raw):
    found = []
    for chip, name in enumerate(CHIPS):
        for bit in range(8):
            asserted = [pc for pc in LOOP if (raw[pc][chip] >> bit) & 1]
            for polarity, pcs in (('high', asserted),
                                  ('low', [pc for pc in LOOP
                                           if pc not in asserted])):
                if len(pcs) == 1:
                    found.append(dict(chip=name, bit=bit,
                                      asserted_level=polarity,
                                      only_pc=f'{pcs[0]:03X}'))
    return found


def output_stats(outputs):
    stats = []
    for pc in LOOP:
        values = outputs[pc]
        increments = Counter((b - a) & 255 for a, b in
                             zip(values, values[1:]))
        stats.append(dict(pc=f'{pc:03X}', visits=len(values),
                          distinct_y=len(set(values)),
                          delta_plus_one=increments[1],
                          delta_minus_one=increments[255],
                          delta_zero=increments[0],
                          most_common_delta=increments.most_common(1)[0][0]))
    return stats


def run(out=HERE / 'results/joint-upper-ram-bus-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    generator = random.Random(0x3557)
    inputs = {'held': [127] * VISITS,
              'varying': [generator.randrange(80, 177) for _ in range(VISITS)]}
    cases = []
    for name, offered in inputs.items():
        raw, outputs, digest = capture(mapping, base, offered)
        cases.append(dict(name=name, trace_digest=digest,
                          adc_sha256=hashlib.sha256(bytes(offered)).hexdigest(),
                          raw_by_pc={f'{pc:03X}': [f'{value:02X}' for value in raw[pc]]
                                     for pc in LOOP},
                          single_pc_raw_bits=sites(raw),
                          y_by_pc=output_stats(outputs)))
        print(name, cases[-1]['single_pc_raw_bits'], flush=True)
    if cases[0]['raw_by_pc'] != cases[1]['raw_by_pc']:
        raise ValueError('receive-loop control words depended on ADC input')
    paths = [Path(__file__), PHOTO,
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='direct PROM strobe and Y-address candidates for DSC 3557 RAM',
                  fixture=dict(mapping='joint upper-source mask 08',
                               visits=VISITS, microinstructions=CYCLES,
                               loop=[f'{pc:03X}' for pc in LOOP],
                               adc='held 127 versus deterministic varying 80..176'),
                  cases=cases,
                  limitations=['The DSC 3557 RAM, address counter/mux and data paths are not wired into this emulator.',
                               'A decoded or inverted control can still make a write pulse even without a bare active-low PROM bit.',
                               'An external counter can supply an address even if no Am2901 Y byte increments directly.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
