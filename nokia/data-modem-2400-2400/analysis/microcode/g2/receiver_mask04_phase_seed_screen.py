"""Test initial Q and R5 seeds as mask-04 carrier-phase adjustments."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES, gate_high
from receiver_mask04_carrier_phase_screen import rotated_transmit
from receiver_mask04_phase47_logic import score
from receiver_mask04_rowpair_phase_code import row_pairs
from reference_modem import receive

PRIOR = HERE / 'results/receiver-mask04-carrier-phase-screen.json'
SEED = 0x5A17
CARRIER_PHASE_DEGREES = 45
Q_VALUES = (0, 5, 10, 15)
R5_VALUES = (0, 0x40, 0x80, 0xC0)
VISITS_PER_SYMBOL = 375
FIXED_CAPTURE_PHASE = 47


def capture_seed(mapping, base, middle, q, r5):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, CARRIER_PHASE_DEGREES)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference input lost dibits')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC hold schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    # The scenario builder deliberately seeds Q=5. Override after it runs;
    # changing base['initial']['q'] would not change the executed fixture.
    scenario['initial']['q'] = q
    scenario['initial']['ram'][5] = r5
    captured = []
    previous_high = False
    previous_y = None
    high_count = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary,
                         trace_limit=CYCLES if q == 5 else 0)
        if not result['clean'] or result['completed_cycles'] != CYCLES:
            raise ValueError('seeded execution stopped')
        if q != 5:
            return None, dict(trace_digest=result['trace_digest'],
                              executed_initial_q=q,
                              executed_initial_r5=r5,
                              receiver_adc_visits=result['address_counts'].get(
                                  0x3F8, 0),
                              receiver_output_visits=result['address_counts'].get(
                                  0x3ED, 0),
                              final_pc=f"{result['final_state']['pc']:03X}")
        if (result['address_counts'].get(0x3ED, 0) != 4 * ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS):
            raise ValueError('Q=5 receive loop did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            high = gate_high(row)
            if high:
                if row['pc'] != 0x3ED:
                    raise ValueError('PROM gate moved')
                high_count += 1
            if previous_high and not high:
                captured.append(previous_y)
            previous_high, previous_y = high, row['alu']['y']
    if high_count != 4 * ADC_VISITS or len(captured) != high_count:
        raise ValueError('seeded latch edge count changed')
    return captured, dict(trace_digest=result['trace_digest'],
                          captured_sha256=hashlib.sha256(bytes(captured)).hexdigest(),
                          executed_initial_q=q,
                          executed_initial_r5=r5,
                          receiver_adc_visits=ADC_VISITS,
                          receiver_output_visits=4 * ADC_VISITS,
                          final_pc=f"{result['final_state']['pc']:03X}")


def run(out=HERE / 'results/receiver-mask04-phase-seed-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(16)]
    cases = []
    for role, values in (('Q', Q_VALUES), ('R5', R5_VALUES[1:])):
        for value in values:
            q = value if role == 'Q' else 5
            r5 = value if role == 'R5' else 0
            captured, trace = capture_seed(mapping, base, middle, q, r5)
            if captured is None:
                cases.append(dict(seed_role=role, initial_value=value,
                                  receiver_reached=False, **trace))
                print('unreached', role, value, trace['final_pc'], flush=True)
            else:
                rows = row_pairs(captured)
                errors = [score([rows[VISITS_PER_SYMBOL * symbol + phase]
                                 for symbol in range(16)], middle)['errors']
                          for phase in range(VISITS_PER_SYMBOL)]
                cases.append(dict(seed_role=role, initial_value=value,
                                  receiver_reached=True,
                                  fixed_phase_errors=errors[FIXED_CAPTURE_PHASE],
                                  min_errors_over_capture_phase=min(errors),
                                  zero_error_phase_count=errors.count(0),
                                  **trace))
                print('captured', role, value, errors[FIXED_CAPTURE_PHASE],
                      min(errors), flush=True)
    q_cases = [case for case in cases if case['seed_role'] == 'Q']
    prior = next(case for case in json.loads(PRIOR.read_text())['cases']
                 if case['carrier_phase_degrees'] == CARRIER_PHASE_DEGREES
                 and case['seed'] == SEED)
    baseline = next(case for case in q_cases if case['initial_value'] == 5)
    if (baseline['captured_sha256'] != prior['captured_sha256'] or
            baseline['fixed_phase_errors'] != prior['fixed_phase_errors'] or
            baseline['min_errors_over_capture_phase'] !=
            prior['minimum_errors']):
        raise ValueError('baseline rotated-carrier trace changed')
    paths = (Path(__file__), PRIOR,
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='initial Q/R5 carrier-phase seed screen under fixed mask-04 receive fixture',
                  fixture=dict(carrier_phase_degrees=CARRIER_PHASE_DEGREES,
                               dibit_seed=SEED,
                               initial_q_values=Q_VALUES,
                               initial_r5_values=R5_VALUES,
                               scenario_default_q=5,
                               base_initial_r5=base['initial']['ram'][5],
                               capture_phases=VISITS_PER_SYMBOL,
                               fixed_capture_phase=FIXED_CAPTURE_PHASE),
                  cases=cases,
                  limitations=['Initial Q is an entry selector in this fixture; other values do not reach the receive loop, so they do not test an in-loop phase adjustment.',
                               'Only initial state is varied; a time-varying carrier-control input is not tested.',
                               'These four R5 values and four Q values do not exhaust register seeds.',
                               'The Boolean decision circuit and physical USART RxD route remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
