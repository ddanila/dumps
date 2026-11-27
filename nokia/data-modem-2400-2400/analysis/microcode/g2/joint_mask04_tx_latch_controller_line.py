"""Compare DAC latch topologies on saved executed-8031 A4 bytes."""

import hashlib
import json
from pathlib import Path

from joint_mask04_tx_bank_phase import scenario_for
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from joint_four_row_retention_tx import (
    BUSES, MAPPINGS, SAMPLE_COUNT, SAMPLE_DIVISOR, TXREADY, candidate,
    fixture, mapped, mapping_with_upper_source,
)
from photo_dac_bus_permutations import mapped_codes
from photo_joint_tone_training_data import (
    SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_SYMBOLS, TOTAL_SYMBOLS,
    segment2_from_txd,
)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_joint_line_filter_screen import bandpass
from reference_modem import spectral_peak

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
PRIOR = RESULTS / 'joint-mask04-tx-12a-delayed-latch.json'
OUT = RESULTS / 'joint-mask04-tx-latch-controller-line.json'
TONE_END = TONE_SYMBOLS * 8
SILENCE_END = (TONE_SYMBOLS + SILENCE_SYMBOLS) * 8
QS = (0.5, 1.0)


def score(raw, bus, symbols, q):
    codes = mapped_codes(raw, bus)
    tone = spectral_peak([value - 128 for value in codes[64:TONE_END]],
                         lower=100, upper=3500)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], q)
    decision = decision_result([value + 128 for value in wave[SILENCE_END:]],
                               symbols, sample_shift=6)
    if decision['decisions'] != 62:
        raise ValueError('controller A3/A4 decision count changed')
    return dict(q=q, tone_peak_hz=tone['frequency_hz'],
                wrong=decision['errors'],
                wrong_decision_indices=decision['error_indices'],
                raw_code_sha256=hashlib.sha256(bytes(codes)).hexdigest())


def run(out=OUT):
    controller = json.loads(TXREADY.read_text())
    prior = json.loads(PRIOR.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('DAC bus family changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = capturing_execute()
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    rows = []
    for selector in ('40', '60'):
        source = next(row for row in controller['cases']
                      if row['selector'] == selector)
        result = execute(mapping, scenario_for(base, source, 256), cycles,
                         mode='integrated', trace_limit=0)
        old = next(row for row in prior['cases']
                   if row['selector'] == selector)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['trace_digest'] != old['trace_digests']['256']):
            raise ValueError('executed controller/PROM trace changed')
        y12a, y127 = result['site_y'][0x12A], result['site_y'][0x127]
        if len(y12a) != 312054 or len(y127) != 312054:
            raise ValueError('transmit site visits changed')
        held = [y12a[SAMPLE_DIVISOR * n] for n in range(SAMPLE_COUNT)]
        shared = [y127[SAMPLE_DIVISOR * n + 1] for n in range(SAMPLE_COUNT)]
        for raw, phase in ((held, old['phases'][0]),
                           (shared, old['phases'][1])):
            if hashlib.sha256(bytes(raw)).hexdigest() != phase['banks']['256']['raw_y_sha256']:
                raise ValueError('latch interpretation differs from earlier real-PROM run')
        symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(source)
        bus_rows = []
        for index, bus in enumerate(buses):
            topologies = []
            for name, raw in (('held_12A', held), ('shared_127', shared)):
                scores = [score(raw, bus, symbols, q) for q in QS]
                expected_q1 = old['phases'][0 if name == 'held_12A' else 1][
                    'banks']['256']['bus_scores'][index]['filtered_data_errors']
                if scores[1]['wrong'] != expected_q1:
                    raise ValueError('saved Q=1 topology score changed')
                topologies.append(dict(name=name, scores=scores))
            bus_rows.append(dict(bus_index=index, topologies=topologies))
        expected_q05 = [0, 1 if selector == '40' else 2]
        if any([topology['scores'][0]['wrong'] for topology in bus['topologies']]
               != expected_q05 or any(score['tone_peak_hz'] != 2100.0
                                      for topology in bus['topologies']
                                      for score in topology['scores'])
               for bus in bus_rows):
            raise ValueError('executed-controller latch line result changed')
        rows.append(dict(selector=selector,
                         tx_trace_digest=result['trace_digest'],
                         expected_a4_dibits=symbols[SEGMENT_SYMBOLS:],
                         different_y_samples=sum(a != b for a, b in zip(held, shared)),
                         buses=bus_rows))
        print('controller latch line', selector, 'Q0.5 wrong',
              [(b['bus_index'], [t['scores'][0]['wrong']
                                 for t in b['topologies']])
               for b in bus_rows], flush=True)
    sources = (Path(__file__), PRIOR, TXREADY, BUSES, MAPPINGS['q3'],
               HERE / 'joint_mask04_tx_12a_delayed_latch.py',
               HERE / 'joint_mask04_tx_bank_phase.py',
               HERE / 'photo_joint_tone_training_data.py',
               HERE / 'photo_joint_line_filter_screen.py',
               HERE / 'photo_main_dibit_dac_decode.py',
               HERE / 'reference_modem.py',
               HERE.parent / 'assumed/execute.py',
               *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='executed-8031 A4 line comparison of held-12A and shared-127 DAC latch routes',
                  fixture=dict(controller_source=TXREADY.name,
                               transmitter_bank=256,
                               samples=SAMPLE_COUNT,
                               sample_divisor=SAMPLE_DIVISOR,
                               assumed_a2_output='DAC mid-code mute',
                               fixed_center_hz=1950,
                               q_values=QS,
                               sample_shift=6,
                               surviving_dac_buses=len(buses)),
                  cases=rows,
                  limitations=[
                      'The 8031 bytes were executed in the saved controller fixture, but its timer and ready signals were modeled; the DAC data/clock and analog line remain assumed.',
                      'A known-carrier reference decoder scores the line; it is not an executed DSC receive decision.',
                      'This score covers the A3/A4 segment and does not choose actual latch wiring without an independent pin or line constraint.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
