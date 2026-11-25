"""Replay the frozen row-pair phase code at changed ADC input levels."""

import hashlib
import json
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
from lower_i_d3f8_upper_symbol_screen import sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES, gate_high
from receiver_mask04_rowpair_phase_code import (ADC_VISITS_PER_SYMBOL,
                                                evaluate, row_pairs)
from reference_modem import receive, transmit

PRIOR = HERE / 'results/receiver-mask04-rowpair-phase-code.json'
LEVELS = ((0.75, 0), (1.25, 0), (1.0, 16))
STREAMS = (0, 6)  # one periodic, one nonperiodic


def capture_level(mapping, base, middle, gain, bias):
    dibits = [0] * 8 + middle + [0] * 8
    original = transmit(dibits)
    changed = [max(-127, min(127, round(gain * value + bias)))
               for value in original]
    if receive(changed) != dibits[1:]:
        raise ValueError('changed-level reference waveform lost its dibits')
    samples = [127 - value for value in
               changed[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC hold schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    captured = []
    previous_high = False
    high_count = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3ED, 0) != 4 * ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS):
            raise ValueError('changed-level full-PROM receive path stopped')
        previous_y = None
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            high = gate_high(row)
            if high:
                if row['pc'] != 0x3ED:
                    raise ValueError('PROM gate moved off 3ED')
                high_count += 1
            if previous_high and not high:
                captured.append(previous_y)
            previous_high, previous_y = high, row['alu']['y']
    if high_count != 4 * ADC_VISITS or len(captured) != high_count:
        raise ValueError('changed-level 3ED latch edge count changed')
    return captured, dict(trace_digest=result['trace_digest'],
                          captured_sha256=hashlib.sha256(bytes(captured)).hexdigest(),
                          input_adc_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                          clipped_pcm_samples=sum(abs(round(gain * value + bias)) > 127
                                                  for value in original))


def run(out=HERE / 'results/receiver-mask04-rowpair-level-check.json'):
    prior = json.loads(PRIOR.read_text())
    chosen = prior['selected']
    if (chosen['phase'], chosen['lag'], chosen['orientation'],
            chosen['carrier_offset']) != (0, 0, 1, 2):
        raise ValueError('frozen prior readout changed')
    labels = {(row['row0'], row['row3']): (0, row['phase_quadrant'])
              for row in chosen['codebook']}
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    stimuli = sequences()
    cases = []
    for gain, bias in LEVELS:
        for index in STREAMS:
            middle = stimuli[index]['middle']
            captured, trace = capture_level(mapping, base, middle, gain, bias)
            pairs = row_pairs(captured)
            score = evaluate({index: pairs}, {index: middle}, [index],
                             labels, chosen['phase'], chosen['lag'],
                             chosen['orientation'], chosen['carrier_offset'],
                             ADC_VISITS_PER_SYMBOL)
            cases.append(dict(gain=gain, bias=bias, stream_index=index,
                              score=score,
                              distinct_row_pairs=len(set(pairs)),
                              row1_nonzero=sum(captured[4 * n + 1] != 0
                                               for n in range(ADC_VISITS)),
                              row2_nonzero=sum(captured[4 * n + 2] != 0
                                               for n in range(ADC_VISITS)),
                              **trace))
            print('captured', gain, bias, index, score, flush=True)
    paths = (Path(__file__), PRIOR, HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='frozen mask-04 row-pair phase-code readout under gain and bias changes',
                  fixture=dict(training='eight-state phase codebook from the prior unmodified-level three-stream training only',
                               gains_and_biases=LEVELS, stream_indexes=STREAMS,
                               adc='complement of changed signed PCM, 47/46 visits per sample',
                               full_prom_cycles_per_case=CYCLES),
                  cases=cases,
                  limitations=['The reference matched filter proves the changed-level stimuli remain decodable, not that the DSC output reaches USART RxD.',
                               'The eight-state codebook and differential decision are external; no gain adaptation is modeled.',
                               'ADC routing, four-row dispatch, PROM latch and physical output remain assumptions.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
