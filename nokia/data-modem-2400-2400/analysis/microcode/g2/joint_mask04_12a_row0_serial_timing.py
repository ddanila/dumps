"""Replay candidate receive latch and RxC events from executed PROM snapshots."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_row0_boolean import phase
from receiver_mask04_external_sync_handoff import ExternalSyncReceiver, MODE, SYNC_CHAR, COMMAND

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json'
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
OUT = HERE / 'results/joint-mask04-12a-row0-serial-timing.json'
VISITS_PER_SYMBOL = 375
CYCLES_PER_VISIT = 32
CYCLES_PER_SYMBOL = VISITS_PER_SYMBOL * CYCLES_PER_VISIT
BIT_CYCLES = CYCLES_PER_SYMBOL // 2
ROW0_CYCLE = 50
Y3F8_CYCLE = 63
VARIANTS = {
    'aligned': dict(row_visit='46', row_site='row0', first_visit='46',
                    second_visit='93', first_rxc_cycle=BIT_CYCLES),
    'row_one_visit_late': dict(row_visit='47', row_site='row0', first_visit='46',
                               second_visit='93', first_rxc_cycle=BIT_CYCLES),
    'row3_substitution': dict(row_visit='46', row_site='row3', first_visit='46',
                              second_visit='93', first_rxc_cycle=BIT_CYCLES),
    'first_y_one_visit_late': dict(row_visit='46', row_site='row0', first_visit='47',
                                   second_visit='93', first_rxc_cycle=BIT_CYCLES),
    'second_y_one_visit_late': dict(row_visit='46', row_site='row0', first_visit='46',
                                    second_visit='94', first_rxc_cycle=BIT_CYCLES),
    'rxc_before_second_capture': dict(row_visit='46', row_site='row0',
                                      first_visit='46', second_visit='93',
                                      first_rxc_cycle=3000),
}


def covers_from_model(model):
    return [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                  for cube in row['cubes']) for row in model['phase_bits']]


def captured_phase(symbol, variant, covers):
    visits = symbol['visits']
    first = visits[variant['first_visit']]['y3f8']
    second = visits[variant['second_visit']]['y3f8']
    row = visits[variant['row_visit']][variant['row_site']]
    state = ((first >> 5) & 7) | (((second >> 7) & 1) << 3)
    state |= (((second >> 4) & 1) << 4) | (((second >> 6) & 1) << 5)
    state |= (row & 1) << 6
    row_cycle = (ROW0_CYCLE if variant['row_site'] == 'row0'
                 else ROW0_CYCLE + 24) + int(variant['row_visit']) * CYCLES_PER_VISIT
    first_cycle = Y3F8_CYCLE + int(variant['first_visit']) * CYCLES_PER_VISIT
    second_cycle = Y3F8_CYCLE + int(variant['second_visit']) * CYCLES_PER_VISIT
    return phase(state, covers), max(row_cycle, first_cycle, second_cycle), state


def replay(case, variant, covers, inverse, exe):
    symbols = case['multi_visit_symbols']
    if len(symbols) != handoff.RX_SYMBOLS or len(case['expected_dibits']) != len(symbols):
        raise ValueError('real-PROM symbol count changed')
    captures = [captured_phase(symbol, variant, covers) for symbol in symbols]
    bits = []
    decisions = [3]  # First reversal dibit is known from the offered preamble, not decoded.
    events = []
    for index, (current, ready, state) in enumerate(captures):
        if index:
            previous, previous_ready, _ = captures[index - 1]
            dibit = inverse[(current - previous) & 3]
        else:
            previous_ready = 0
            dibit = 3
        if index:
            decisions.append(dibit)
        for bit_in_symbol in (0, 1):
            edge = index * CYCLES_PER_SYMBOL + variant['first_rxc_cycle'] + bit_in_symbol * BIT_CYCLES
            available = (index == 0 or
                         (index * CYCLES_PER_SYMBOL + ready <= edge and
                          (index - 1) * CYCLES_PER_SYMBOL + previous_ready <= edge))
            bit = ((dibit >> bit_in_symbol) & 1) if available else None
            bits.append(bit)
            if index in (0, 1, handoff.PREAMBLE, handoff.PREAMBLE + 1,
                         len(symbols) - 1):
                events.append(dict(symbol=index, bit=bit_in_symbol,
                                   captured_state=f'{state:02X}',
                                   phase_ready_cycle=index * CYCLES_PER_SYMBOL + ready,
                                   rxc_rising_cycle=edge, rxd=bit))
    wrong = [index for index, (got, want) in enumerate(zip(decisions[1:],
                                                            case['expected_dibits'][1:]), 1)
             if got != want]
    unknown_edges = [index for index, bit in enumerate(bits) if bit is None]
    recovered = None
    result = None
    if not unknown_edges:
        receiver = ExternalSyncReceiver(MODE, SYNC_CHAR, COMMAND)
        recovered = []
        for index, bit in enumerate(bits):
            receiver.rising_rxc(index, bit, index == handoff.DATA_START_BIT)
            if receiver.read_status() & 2:
                recovered.append(receiver.read_data())
        if len(recovered) != 8:
            raise ValueError('aligned external sync did not assemble eight characters')
        selector = case['selector']
        delay = 5 if selector == '40' else 18
        result = handoff.controller(exe, delay, int(selector, 16),
                                    handoff.DATA_START_BIT, recovered)
    offered = [int(value, 16) for value in case['offered_line_bytes']]
    return dict(wrong_decision_indices=wrong, unknown_rxc_edges=unknown_edges,
                recovered_line_bytes=([f'{value:02X}' for value in recovered]
                                      if recovered is not None else None),
                recovered_matches_offered=(recovered == offered
                                           if recovered is not None else None),
                controller_state=(f'{result["state"]:02X}' if result else None),
                controller_errors=(result['errors'] if result else None),
                controller_overruns=(result['overruns'] if result else None),
                controller_consumed_bytes=(result['consumed_bytes'] if result else None),
                controller_decoded_bytes=(result['decoded_bytes'] if result else None),
                minimum_setup_cycles=min(variant['first_rxc_cycle'] - ready,
                                         variant['first_rxc_cycle'] + BIT_CYCLES - ready),
                selected_events=events)


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    model = json.loads(LOGIC.read_text())
    covers = covers_from_model(model)
    inverse = {step: dibit for dibit, step in enumerate(model['fixture']['phase_convention'])}
    if len(source['cases']) != 6 or len(inverse) != 4:
        raise ValueError('frozen PROM holdout changed')
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        for case in source['cases']:
            variants = {name: replay(case, variant, covers, inverse, exe)
                        for name, variant in VARIANTS.items()}
            aligned = variants['aligned']
            if (aligned['wrong_decision_indices'] or aligned['unknown_rxc_edges'] or
                    not aligned['recovered_matches_offered'] or
                    aligned['controller_errors'] or aligned['controller_overruns'] or
                    aligned['controller_consumed_bytes'] != [int(x, 16) for x in
                                                             case['offered_line_bytes']] or
                    aligned['controller_decoded_bytes'] != [int(x, 16) for x in
                                                            case['payload']] or
                    variants['row_one_visit_late']['wrong_decision_indices'] or
                    not variants['rxc_before_second_capture']['unknown_rxc_edges'] or
                    not all(variants[name]['wrong_decision_indices'] for name in
                            ('row3_substitution', 'first_y_one_visit_late',
                             'second_y_one_visit_late'))):
                raise ValueError(('latch/serial control changed', case['selector'], case['level']))
            cases.append(dict(selector=case['selector'], level=case['level'],
                              payload=case['payload'], rx_trace_digest=case['rx_trace_digest'],
                              variants=variants))
            print('timing', case['selector'], case['level'],
                  {name: (len(row['wrong_decision_indices']),
                          len(row['unknown_rxc_edges']))
                   for name, row in variants.items()}, flush=True)
    paths = (Path(__file__), SOURCE, LOGIC,
             HERE / 'joint_mask04_12a_row0_boolean.py',
             HERE / 'receiver_mask04_external_sync_handoff.py',
             HERE / 'joint_mask04_buffered_serial_handoff.py')
    report = dict(experiment='candidate row/first/second capture timing into RxD/RxC and modeled 8251/8031',
                  fixture=dict(real_prom_cases=6, visits_per_symbol=VISITS_PER_SYMBOL,
                               cycles_per_visit=CYCLES_PER_VISIT,
                               assumed_row0_first_cycle=ROW0_CYCLE,
                               assumed_y3f8_first_cycle=Y3F8_CYCLE,
                               bit_cycles=BIT_CYCLES,
                               external_syndet_at_bit=handoff.DATA_START_BIT,
                               assumed_first_dibit=3, variants=VARIANTS,
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'This event replay uses snapshots from earlier real-PROM executions, not a traced physical latch or new PROM execution.',
                      'U12 has four storage bits; this seven-bit state requires additional untraced storage and capture qualification.',
                      'ADC, capture clock, phase gates, RxD/RxC and SYNDET connections remain labelled circuit assumptions.',
                      'The 8251 model covers external-sync receive and immediate reads; it is not the complete device.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
