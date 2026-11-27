"""Replay a paired-LS75 transfer schedule for the thirteen-bit receiver."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_row0_serial_timing as serial
from execute import execute
from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import FEATURES, STEPS
from joint_mask04_12a_modebit97_staged_capture import FRESH, INVENTORY
from joint_mask04_12a_modebit102_gain095_feature_screen import GAIN105, GAIN095
from receiver_four_row_condition_screen import configured

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OUT = RESULTS / 'joint-mask04-12a-modebit156-staged-transfer.json'
THIRTEEN = FEATURES + (('141', 'y3f8', 6),)
U28_LOAD_CYCLE = 5000


def staged_state(symbol):
    visits = symbol['visits']
    first = visits['46']['y3f8']
    second = visits['93']['y3f8']
    early_row = visits['47']['row0']
    late_row = visits['93']['row0']
    later = visits['94']['y3f8']
    last = visits['141']['y3f8']
    # U14 pair A captures first Y5/Y6. Pair B initially captures first Y7.
    u14_a = (first >> 5) & 3
    u14_b_early_y7 = (first >> 7) & 1
    # U3's common visit-93 enable copies that U14 Q before pair B is
    # overwritten at visit 94, alongside the three second-Y bits.
    u3_transferred_y7 = u14_b_early_y7
    u3_second = (((second >> 7) & 1) |
                 (((second >> 4) & 1) << 1) |
                 (((second >> 6) & 1) << 2))
    u14_b_later = (((later >> 4) & 1) |
                   (((later >> 7) & 1) << 1))
    u12_early = (early_row & 3) | ((visits['46']['mode_bit5'] & 1) << 2)
    u25_late_row = (late_row >> 2) & 1
    u25_last_y6 = (last >> 6) & 1
    return (u14_a | (u3_transferred_y7 << 2) | (u3_second << 3) |
            ((u12_early & 3) << 6) | ((u14_b_later & 1) << 8) |
            (((u12_early >> 2) & 1) << 9) | (u25_late_row << 10) |
            (((u14_b_later >> 1) & 1) << 11) | (u25_last_y6 << 12))


def transient_y_probe():
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    scenario = configured(base, [127] * 1000, 'previous', 'overflow', 1)
    scenario['io']['read']['pc_sequences'][str(0x3EB)] = [0x81] * 1000
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, 6000, mode='integrated',
                         out=temporary, trace_limit=6000)
        if not result['clean'] or result['completed_cycles'] != 6000:
            raise ValueError('short real-PROM Y-bus probe stopped')
        selected = {}
        for index, raw in enumerate((Path(temporary) / 'trace.jsonl').open()):
            if index in (4574, 4575, 4576):
                row = json.loads(raw)
                selected[index] = dict(pc=f"{row['pc']:03X}", y=row['alu']['y'])
    if (selected[4575]['pc'], selected[4576]['pc'],
            selected[4575]['y'] == selected[4576]['y']) != ('3F8', '3F9', False):
        raise ValueError('late Y is no longer a one-cycle bus value')
    return selected


def run(out=OUT):
    cases = []
    paths = []

    def append(path, edge):
        paths.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append(case)

    for path in (*CAPTURES, *RAW):
        append(path, lambda case, path=path: boundary(path, case))
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            append(path, None if mode == 'held81' else
                   48 if mode == 'edge48' else 32)
    for mode, path in zip(('edge32', 'edge48'), FAILED_189):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), FRESH):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), GAIN105):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), GAIN095):
        append(path, 32 if mode == 'edge32' else 48)
    if len(cases) != 108 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('staged-transfer stream population changed')
    inventory = {part['ref']: part['marking'] for part in
                 json.loads(INVENTORY.read_text())['parts']}
    expected = dict(U3='74LS373 PC', U12='SN74LS175N',
                    U14='SN74LS75N', U25='HD74LS74AP', U28='74LS169AN')
    if {ref: inventory.get(ref) for ref in expected} != expected:
        raise ValueError('photographed storage package population changed')
    mismatches = 0
    u14_pair_reenable_changes = {str(bit): 0 for bit in (5, 6, 7)}
    for case in cases:
        for symbol in case['multi_visit_symbols']:
            mismatches += staged_state(symbol) != code(symbol, THIRTEEN)
            delta = symbol['visits']['46']['y3f8'] ^ symbol['visits']['94']['y3f8']
            for bit in (5, 6, 7):
                u14_pair_reenable_changes[str(bit)] += bool(delta & (1 << bit))
    graph = solve(cases, THIRTEEN, STEPS)
    if (mismatches or graph['state_codes'] != 156 or
            graph['components'] != [156] or graph['directed_conflicts'] or
            any(not value for value in u14_pair_reenable_changes.values())):
        raise ValueError('staged thirteen-bit capture or graph changed')
    timing = dict(U14_first_pairs=serial.Y3F8_CYCLE + 46 * serial.CYCLES_PER_VISIT,
                  U12_early_row=serial.ROW0_CYCLE + 47 * serial.CYCLES_PER_VISIT,
                  U25_late_row=serial.ROW0_CYCLE + 93 * serial.CYCLES_PER_VISIT,
                  U3_second_and_transfer=serial.Y3F8_CYCLE + 93 * serial.CYCLES_PER_VISIT,
                  U14_pair_B_overwrite=serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT,
                  U25_late_y6=serial.Y3F8_CYCLE + 141 * serial.CYCLES_PER_VISIT,
                  U28_assumed_load=U28_LOAD_CYCLE,
                  first_RxC=serial.BIT_CYCLES,
                  second_RxC=serial.CYCLES_PER_SYMBOL)
    if timing != dict(U14_first_pairs=1535, U12_early_row=1554,
                      U25_late_row=3026, U3_second_and_transfer=3039,
                      U14_pair_B_overwrite=3071, U25_late_y6=4575,
                      U28_assumed_load=5000, first_RxC=6000,
                      second_RxC=12000):
        raise ValueError('modeled thirteen-bit event order changed')
    probe = transient_y_probe()
    sources = (Path(__file__), INVENTORY,
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_modebit97_staged_capture.py',
               HERE / 'joint_mask04_12a_modebit102_gain095_feature_screen.py',
               HERE / 'joint_mask04_12a_row0_serial_timing.py',
               HERE / 'joint_mask04_12a_buffered_line.py',
               HERE / 'receiver_four_row_condition_screen.py', *paths)
    report = dict(experiment='paired-U14 transfer and U25 late-Y6 capacity replay',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               features=THIRTEEN, packages=expected),
                  proposed_storage=dict(U14_pair_A='first 3F8 Y5/Y6',
                                        U14_pair_B_before_transfer='first 3F8 Y7',
                                        U3_at_visit93='second 3F8 Y7/Y4/Y6 plus transferred first Y7',
                                        U14_pair_B_after_transfer='later 3F8 Y4/Y7',
                                        U12_at_visit47='early row0 Y0/Y1 plus assumed held mode bit',
                                        U25_FF_A='late row0 Y2',
                                        U25_FF_B='visit-141 3F8 Y6'),
                  timing=timing,
                  modeled_late_capture_to_load_cycles=U28_LOAD_CYCLE - timing['U25_late_y6'],
                  modeled_load_to_first_RxC_cycles=timing['first_RxC'] - U28_LOAD_CYCLE,
                  staged_state_mismatches=mismatches,
                  phase_graph=graph,
                  U14_first_bits_changed_by_later_enable=u14_pair_reenable_changes,
                  short_real_PROM_bus_probe=probe,
                  limitations=[
                      'The U14 pair enables, U3 transfer D input, U25 independent clocks and U28 load/data nets are proposed, not traced Nokia connections.',
                      'The short bus probe shows Y changes immediately after the 3F8 event in one held-81 constant-ADC run; the late bit therefore needs U25 storage before a cycle-5000 U28 load.',
                      'Mode-bit hold through the U12 shared clock and the U28 phase/dibit input circuit remain unverified.',
                      'The zero-conflict 156-state graph uses all 108 saved streams, including the 0.95x failures that selected the visit-141 Y6 bit; it is development evidence without a frozen thirteen-bit gate or new holdout.',
                      'Modeled cycle gaps are not measured electrical setup or propagation margins.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('streams', result['fixture']['streams'],
          'staged mismatches', result['staged_state_mismatches'],
          'conflicts', result['phase_graph']['directed_conflicts'])
