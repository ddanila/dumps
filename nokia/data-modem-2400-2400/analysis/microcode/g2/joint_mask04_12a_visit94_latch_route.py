"""Replay an assumed U14/U12/U3 staged receive capture and handoff."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase
from joint_mask04_12a_visit94_phase_gate import candidate_phase
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
INVENTORY = HERE.parent / 'board/inventory.json'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
INPUTS = (
    ('0.80', 133, RESULTS / 'joint-mask04-12a-lowgain133-expanded-visits.json'),
    ('1.15', 131, RESULTS / 'joint-mask04-12a-mode1-expanded-1.15.json'),
    ('1.25', 131, RESULTS / 'joint-mask04-12a-mode1-expanded-1.25.json'),
    ('0.80', 133, RESULTS / 'joint-mask04-12a-visit94-phase-holdout-133.json'),
    ('0.80', 135, RESULTS / 'joint-mask04-12a-visit94-phase-holdout-135.json'),
)
OUT = RESULTS / 'joint-mask04-12a-visit94-latch-route.json'
FIRST_Y_CYCLE = serial.Y3F8_CYCLE + 46 * serial.CYCLES_PER_VISIT
U12_CLOCK = serial.ROW0_CYCLE + 47 * serial.CYCLES_PER_VISIT
SECOND_Y_CYCLE = serial.Y3F8_CYCLE + 93 * serial.CYCLES_PER_VISIT
LATER_Y_CYCLE = serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT


def staged(symbol):
    """Return phase and state after explicit U14 pair reuse/U12 transfer."""
    visits = symbol['visits']
    first = visits['46']['y3f8']
    second = visits['93']['y3f8']
    later = visits['94']['y3f8']
    # U14 pair A holds first Y5 and Y7. Pair B initially holds Y6.
    u14_a_y5 = (first >> 5) & 1
    u14_a_y7 = (first >> 7) & 1
    u14_b_first_y6 = (first >> 6) & 1
    # U12 clocks after the first Y latch: two of its four FFs retain
    # row-0 Y0 and the copied U14 pair-B Y6.
    u12_row0 = visits['47']['row0'] & 1
    u12_first_y6 = u14_b_first_y6
    # U3 closes at visit 93; its common LE holds the three later bits.
    u3_y7 = (second >> 7) & 1
    u3_y4 = (second >> 4) & 1
    u3_y6 = (second >> 6) & 1
    # Pair B can now reopen at visit 94 to capture the additional bit.
    u14_b_later_y6 = (later >> 6) & 1
    state = (u14_a_y5 | u12_first_y6 << 1 | u14_a_y7 << 2 |
             u3_y7 << 3 | u3_y4 << 4 | u3_y6 << 5 | u12_row0 << 6)
    phase = corrected_phase(state, 1) & ~u14_b_later_y6
    return phase, state


def common_enable_phase(symbol):
    """Counterfactual: reopening U14 also overwrites first Y5 and Y7."""
    _, state = staged(symbol)
    later = symbol['visits']['94']['y3f8']
    for state_bit, y_bit in ((0, 5), (2, 7)):
        state = ((state & ~(1 << state_bit)) |
                 (((later >> y_bit) & 1) << state_bit))
    return corrected_phase(state, 1) & ~((later >> 6) & 1)


def run(out=OUT):
    inventory = json.loads(INVENTORY.read_text())
    markings = {part['ref']: part['marking'] for part in inventory['parts']}
    required = {'U3': '74LS373 PC', 'U12': 'SN74LS175N',
                'U14': 'SN74LS75N'}
    if any(markings.get(ref) != value for ref, value in required.items()):
        raise ValueError('photo inventory changed')
    if not FIRST_Y_CYCLE < U12_CLOCK < SECOND_Y_CYCLE < LATER_Y_CYCLE < serial.BIT_CYCLES:
        raise ValueError('capture order no longer fits modeled RxC')
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        def captured(symbol, variant, covers):
            phase, state = staged(symbol)
            return phase, LATER_Y_CYCLE, state
        with patch.object(serial, 'captured_phase', captured):
            for gain, offset, path in INPUTS:
                saved = json.loads(path.read_text())
                for case in saved['cases']:
                    symbols = case['multi_visit_symbols']
                    mismatches = [i for i, symbol in enumerate(symbols)
                                  if staged(symbol)[1] != sample_state(symbol, SELECTED)
                                  or staged(symbol)[0] != candidate_phase(symbol)]
                    row_differences = [i for i, symbol in enumerate(symbols)
                                       if (symbol['visits']['46']['row0'] ^
                                           symbol['visits']['47']['row0']) & 1]
                    if mismatches or row_differences or len(symbols) != 65:
                        raise ValueError(('staged bits differ', path.name,
                                          case['selector'], mismatches,
                                          row_differences))
                    payload = [int(value, 16) for value in case['payload']]
                    selector = case['selector']
                    offered = line_octets(payload, 5 if selector == '40' else 18)
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                    common_phases = [common_enable_phase(symbol)
                                     for symbol in symbols]
                    common_wrong = [index for index in range(1, len(symbols))
                                    if inverse[(common_phases[index] -
                                                common_phases[index - 1]) & 3]
                                    != case['expected_dibits'][index]]
                    if (score['wrong_decision_indices'] or
                            not score['recovered_matches_offered'] or
                            score['controller_decoded_bytes'] != payload or
                            score['controller_errors'] or
                            score['controller_overruns'] or
                            len(common_wrong) < 20):
                        raise ValueError(('staged handoff differs', path.name,
                                          selector, score))
                    cases.append(dict(source=path.name, gain=gain,
                                      carrier_offset=offset, selector=selector,
                                      symbols=len(symbols),
                                      state_mismatches=0, row_bit_mismatches=0,
                                      errors=0, exact_line_and_controller=True,
                                      common_enable_wrong_indices=common_wrong,
                                      minimum_setup_cycles=score['minimum_setup_cycles'],
                                      rx_trace_digest=case['rx_trace_digest']))
    paths = (Path(__file__), INVENTORY, MODEL,
             HERE / 'joint_mask04_12a_visit94_phase_gate.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py',
             *(path for _, _, path in INPUTS))
    report = dict(experiment='staged U14/U12/U3 visit-94 receive route',
                  fixture=dict(
                      packages=required,
                      u14_pair_a='first 3F8 Y5,Y7 at visit 46; hold through decision',
                      u14_pair_b='first 3F8 Y6 at visit 46; later 3F8 Y6 at visit 94',
                      u12='row-0 Y0 and copied U14 pair-B first Y6 at visit 47',
                      u3='second 3F8 Y7,Y4,Y6 at visit 93',
                      cycles=dict(first_y=FIRST_Y_CYCLE,
                                  u12_clock=U12_CLOCK,
                                  second_y=SECOND_Y_CYCLE,
                                  later_y=LATER_Y_CYCLE,
                                  first_rxc=serial.BIT_CYCLES),
                      controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'Package capacities and paired enables permit this route, but the specific data and enable nets, pulse widths and electrical timing are not traced.',
                      'The phase-bit gate package and USART RxD/RxC/SYNDET route remain unassigned.',
                      'All ten streams were already used in the gate development or holdout; this is a storage-capacity replay, not a new decision holdout.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print(len(report['cases']), report['fixture']['cycles'])
