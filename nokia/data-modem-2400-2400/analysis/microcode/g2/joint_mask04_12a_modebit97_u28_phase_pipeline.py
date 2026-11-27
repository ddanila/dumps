"""Test one synchronous four-bit U28 phase/dibit register schedule."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_row0_serial_timing as serial
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import STEPS, gate_phase
from joint_mask04_12a_modebit97_staged_capture import (
    FRESH, INVENTORY, RESULTS, staged_twelve_bit_code,
)

HERE = Path(__file__).resolve().parent
OUT = RESULTS / 'joint-mask04-12a-modebit97-u28-phase-pipeline.json'
LOAD_CYCLE = 4500
LATE_READY_CYCLE = serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT
FIRST_RXC_CYCLE = serial.BIT_CYCLES
SECOND_RXC_CYCLE = serial.CYCLES_PER_SYMBOL


def run(out=OUT):
    cases = []
    sources = [Path(__file__), INVENTORY,
               HERE / 'joint_mask04_12a_modebit97_staged_capture.py',
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_row0_serial_timing.py',
               HERE / 'joint_mask04_12a_modebit70_level_feature_screen.py',
               HERE / 'joint_mask04_12a_modebit91_gain110_diagnosis.py']

    def append(path, edge):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append((path, case))

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
    if len(cases) != 100 or any(len(case['multi_visit_symbols']) != 65
                                for _, case in cases):
        raise ValueError('pipeline stream population changed')
    inventory = {part['ref']: part['marking'] for part in
                 json.loads(INVENTORY.read_text())['parts']}
    if inventory.get('U28') != '74LS169AN':
        raise ValueError('photographed U28 package changed')
    if not (LATE_READY_CYCLE == 3071 < LOAD_CYCLE < FIRST_RXC_CYCLE == 6000
            < SECOND_RXC_CYCLE == 12000):
        raise ValueError('pipeline event order changed')

    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    total_decision_errors = 0
    total_serial_bit_errors = 0
    early_load_bit_errors = 0
    late_load_first_bit_errors = 0
    early_mask = sum(1 << bit for bit in (0, 1, 2, 6, 7, 9))
    for path, case in cases:
        register = None  # U28 Q[1:0]=old phase, Q[3:2]=outgoing dibit.
        wrong_decisions = []
        wrong_serial_bits = []
        events = []
        states = [staged_twelve_bit_code(symbol)
                  for symbol in case['multi_visit_symbols']]
        early_register = None
        late_register = None
        for index, state in enumerate(states):
            phase = gate_phase(state)
            if register is None:
                dibit = 3  # Known preamble reversal; not inferred from a prior symbol.
            else:
                dibit = inverse[(phase - (register & 3)) & 3]
            # One synchronous parallel load reads old Q and updates all four Q
            # bits only after its edge. The count inputs are assumed inhibited.
            register = phase | (dibit << 2)
            if index and dibit != case['expected_dibits'][index]:
                wrong_decisions.append(index)
            for bit_in_symbol, edge_in_symbol in ((0, FIRST_RXC_CYCLE),
                                                   (1, SECOND_RXC_CYCLE)):
                bit = (register >> (2 + bit_in_symbol)) & 1
                expected_bit = (case['expected_dibits'][index] >> bit_in_symbol) & 1
                if index == 0:
                    expected_bit = (3 >> bit_in_symbol) & 1
                if bit != expected_bit:
                    wrong_serial_bits.append(2 * index + bit_in_symbol)
                if index in (0, 1, 32, 48, 64):
                    events.append(dict(symbol=index, load_cycle=index * serial.CYCLES_PER_SYMBOL + LOAD_CYCLE,
                                       rxc_cycle=index * serial.CYCLES_PER_SYMBOL + edge_in_symbol,
                                       phase=phase, dibit=dibit, rxd=bit))
            if index:
                mixed = (state & early_mask) | (states[index - 1] & ~early_mask)
                early_phase = gate_phase(mixed)
                early_dibit = inverse[(early_phase - (early_register & 3)) & 3]
            else:
                early_phase, early_dibit = phase, 3
            early_register = early_phase | (early_dibit << 2)
            early_load_bit_errors += sum(
                ((early_register >> (2 + bit)) & 1) !=
                ((case['expected_dibits'][index] >> bit) & 1)
                for bit in (0, 1) if index)
            if index:
                prior_output_bit0 = (late_register >> 2) & 1
                late_load_first_bit_errors += (
                    prior_output_bit0 != (case['expected_dibits'][index] & 1))
                late_dibit = inverse[(phase - (late_register & 3)) & 3]
            else:
                late_dibit = 3
            late_register = phase | (late_dibit << 2)
        total_decision_errors += len(wrong_decisions)
        total_serial_bit_errors += len(wrong_serial_bits)
        checks.append(dict(source=path.name, selector=case.get('selector'),
                           wrong_decision_indices=wrong_decisions,
                           wrong_serial_bit_indices=wrong_serial_bits,
                           selected_events=events if path in FRESH else []))
    if total_decision_errors or total_serial_bit_errors:
        raise ValueError(('U28 pipeline differs from expected symbols',
                          total_decision_errors, total_serial_bit_errors))
    if not early_load_bit_errors or not late_load_first_bit_errors:
        raise ValueError('pipeline timing controls no longer discriminate')
    report = dict(experiment='assumed U28 four-bit synchronous phase and dibit pipeline',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               decisions=64 * len(cases), serial_bits=130 * len(cases),
                               phase_convention=STEPS,
                               U28_QA_QB='current phase, becomes old phase next symbol',
                               U28_QC_QD='current outgoing dibit, bit 0 then bit 1'),
                  timing=dict(last_capture_cycle=LATE_READY_CYCLE,
                              assumed_U28_load_cycle=LOAD_CYCLE,
                              first_RxC_cycle=FIRST_RXC_CYCLE,
                              second_RxC_cycle=SECOND_RXC_CYCLE,
                              modeled_capture_to_load_cycles=LOAD_CYCLE - LATE_READY_CYCLE,
                              modeled_load_to_first_RxC_cycles=FIRST_RXC_CYCLE - LOAD_CYCLE),
                  decision_errors=total_decision_errors,
                  serial_bit_errors=total_serial_bit_errors,
                  timing_controls=dict(
                      early_load_at_cycle_3000_bit_errors=early_load_bit_errors,
                      early_load_compares_bits=2 * 64 * len(cases),
                      late_load_at_cycle_6500_first_bit_errors=late_load_first_bit_errors,
                      late_load_compares_first_bits=64 * len(cases)),
                  checks=checks,
                  limitations=[
                      'U28 parallel-load capacity follows 74LS169-family behavior; its Nokia input, load, clock, count-inhibit and output nets are not traced.',
                      'This event replay uses saved real-PROM symbol snapshots and an assumed mode bit; it is not a new PROM execution or a complete phase-gate circuit.',
                      'The 1,429/1,500-cycle gaps are modeled event intervals, not measured electrical setup or propagation margins.',
                      'The RxD bit-select mux, RxC and SYNDET sources and controller handoff remain separate assumptions.',
                      'The first dibit is supplied from the known preamble, not computed from an unobserved preceding phase.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('streams', result['fixture']['streams'],
          'decision errors', result['decision_errors'],
          'serial bit errors', result['serial_bit_errors'])
