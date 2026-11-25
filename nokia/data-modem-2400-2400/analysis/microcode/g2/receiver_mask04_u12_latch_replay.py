"""Replay two explicitly assumed U12 clocks against executed 3ED events."""

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
from lower_i_d3f8_upper_symbol_screen import SYMBOL_INDEXES
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES, gate_high
from receiver_mask04_carrier_phase_screen import rotated_transmit
from receiver_mask04_phase47_logic import phase_quadrant
from reference_modem import QUADRANT_TO_DIBIT, receive

SEED = 0x5A17
CAPTURE_VISIT = 47
VISITS_PER_SYMBOL = 375


def replay(mapping, base, middle, degrees):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost input dibits')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC visit schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    latch_clock_every_row = 0
    latch_clock_row0 = 0
    rows_per_visit = []
    events = 0
    previous = None
    first_event_cycles = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3ED) != 4 * ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
            raise ValueError('full-PROM receiver path stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if previous is not None and gate_high(previous) and not gate_high(row):
                if previous['pc'] != 0x3ED:
                    raise ValueError('raw-PROM 3ED gate moved')
                row_index = events % 4
                value = previous['alu']['y']
                if len(first_event_cycles) < 8:
                    first_event_cycles.append(previous['cycle'])
                if row_index == 0:
                    latch_clock_row0 = value & 15
                elif row_index in (1, 2) and value != 0:
                    raise ValueError('intervening 3ED row is not zero')
                if row_index == 3:
                    rows_per_visit.append((latch_clock_row0, value & 7,
                                           latch_clock_every_row, value & 7))
                latch_clock_every_row = value & 15
                events += 1
            previous = row
    if events != 4 * ADC_VISITS or len(rows_per_visit) != ADC_VISITS:
        raise ValueError('latch edge count changed')
    scores = {}
    symbol_values = {}
    for name, columns in (('row0_qualified', (0, 1)),
                          ('unqualified_every_row', (2, 3))):
        phases = [phase_quadrant(*(rows_per_visit[
            symbol * VISITS_PER_SYMBOL + CAPTURE_VISIT][column]
            for column in columns)) for symbol in range(16)]
        decisions = [QUADRANT_TO_DIBIT[(phases[symbol] -
                     phases[symbol - 1] - 2) & 3]
                     for symbol in SYMBOL_INDEXES]
        scores[name] = dict(errors=sum(decision != middle[symbol] for
                                       decision, symbol in
                                       zip(decisions, SYMBOL_INDEXES)),
                            checks=len(SYMBOL_INDEXES), dibits=decisions)
        symbol_values[name] = phases
    return dict(degrees=degrees, trace_digest=result['trace_digest'],
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                events=events, first_event_cycles=first_event_cycles,
                first_visit_rows=rows_per_visit[:4], scores=scores,
                phases=symbol_values)


def run(out=HERE / 'results/receiver-mask04-u12-latch-replay.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(16)]
    cases = [replay(mapping, base, middle, degrees) for degrees in (0, 45)]
    nominal = json.loads((HERE / 'results/receiver-mask04-phase47-logic.json').read_text())
    rotated = json.loads((HERE / 'results/receiver-mask04-carrier-phase-screen.json').read_text())
    old_nominal = next(case for case in nominal['fresh_cases']
                       if (case['seed'], case['gain'], case['bias']) ==
                       (SEED, 1.0, 0))
    old_rotated = next(case for case in rotated['cases']
                       if (case['seed'], case['carrier_phase_degrees']) ==
                       (SEED, 45))
    if (cases[0]['trace_digest'] != old_nominal['trace_digest'] or
            cases[1]['trace_digest'] != old_rotated['trace_digest'] or
            cases[0]['scores']['row0_qualified'] != old_nominal['score'] or
            cases[1]['scores']['row0_qualified']['errors'] !=
            old_rotated['fixed_phase_errors']):
        raise ValueError('latch replay differs from prior full-PROM fixtures')
    paths = (Path(__file__), HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='hypothetical U12 row-0 latch versus unqualified 3ED clock',
                  seed=SEED, middle_dibits=middle, capture_visit=CAPTURE_VISIT,
                  cases=cases,
                  assumptions=[
                      'Raw PROM 3ED decode feeds an external clock gate; its physical route is untraced.',
                      'An external modulo-four row counter identifies row 0; U24 is only a photo-compatible candidate.',
                      'U12 holds the low four Y bits on row 0 until row 3, where another external gate uses live Y bits 0..2.',
                      'Previous-symbol phase storage, dibit logic, serialization and USART-01 RxD route are untraced hypotheses.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
