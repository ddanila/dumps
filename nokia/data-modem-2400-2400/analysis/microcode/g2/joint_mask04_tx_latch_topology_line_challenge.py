"""Score two DAC latch topologies on fresh modeled line-side data."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
from joint_mask04_12a_extended_shift import SAMPLES, TX_CYCLES
from joint_mask04_12a_fixed_gain_phase import line_wave, window_at, pcm_at
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
BUSES = line.BUSES
OUT = RESULTS / 'joint-mask04-tx-latch-topology-line-challenge.json'
DIVISOR = 375
PAYLOADS = {
    '40': (0xE3, 0x47, 0xB9, 0x1C, 0x6A, 0xD5, 0x08, 0xF2),
    '60': (0x29, 0xC4, 0x7D, 0xA0, 0x56, 0xEB, 0x13, 0x8F),
}
LEVELS = (0.75, 1.0, 1.25)


def run(out=OUT):
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    gains = json.loads(GAIN.read_text())
    if len(buses) != 6 or gains['fixture']['q'] != 0.5:
        raise ValueError('frozen analog/bus fixture changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    rows = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets(PAYLOADS[selector], delay)
        with patch.object(line, 'SAMPLES', SAMPLES), \
                patch.object(line, 'TX_CYCLES', TX_CYCLES):
            result, held, expected = line.transmitter(execute, mapping, base,
                                                       offered)
        live = result['site_y'][0x127]
        if len(held) != SAMPLES or len(live) < DIVISOR * (SAMPLES - 1) + 2:
            raise ValueError('transmit sample capture changed')
        shared = [live[DIVISOR * n + 1] for n in range(SAMPLES)]
        if held == shared or result['address_counts'].get(0x127) != len(live):
            raise ValueError('latch topology control changed')
        prior = next(row for row in gains['cases'] if row['selector'] == selector)
        bus_rows = []
        for index, bus in enumerate(buses):
            gain = prior['bus_cases'][index]['gain']
            topologies = []
            for name, raw in (('held_12A', held), ('shared_127', shared)):
                wave = line_wave(raw, bus)
                selected = window_at(wave, 6)
                scores = []
                for level in LEVELS:
                    pcm = pcm_at(selected, gain * level)
                    actual = receive(pcm)
                    wrong = [symbol for symbol, (got, want) in enumerate(
                        zip(actual, expected[1:]), 1) if got != want]
                    if len(actual) != 64:
                        raise ValueError('reference symbol count changed')
                    scores.append(dict(level=level, wrong=len(wrong),
                                       wrong_symbol_indices=wrong,
                                       clipped_samples=sum(abs(value) == 127
                                                           for value in pcm),
                                       pcm_sha256=hashlib.sha256(bytes(
                                           value + 127 for value in pcm)).hexdigest()))
                topologies.append(dict(name=name,
                                       raw_y_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                                       scores=scores))
            bus_rows.append(dict(bus_index=index, gain=gain,
                                 topologies=topologies))
        rows.append(dict(selector=selector,
                         payload=[f'{value:02X}' for value in PAYLOADS[selector]],
                         offered_line_bytes=[f'{value:02X}' for value in offered],
                         tx_trace_digest=result['trace_digest'],
                         samples=SAMPLES,
                         differing_y_samples=sum(a != b for a, b in zip(held, shared)),
                         buses=bus_rows))
        expected_shared_errors = 5 if selector == '40' else 1
        if any([next(score['wrong'] for score in topology['scores']
                     if score['level'] == 1.0)
                for topology in bus['topologies']] != [0, expected_shared_errors]
               or any(next(score['clipped_samples'] for score in topology['scores']
                           if score['level'] == 1.0)
                      for topology in bus['topologies'])
               for bus in bus_rows):
            raise ValueError('fresh latch-topology line discriminator changed')
        print('latch topology', selector, 'Y differences',
              rows[-1]['differing_y_samples'],
              'wrong at nominal', [(b['bus_index'],
                 [next(s['wrong'] for s in t['scores'] if s['level'] == 1.0)
                  for t in b['topologies']]) for b in bus_rows], flush=True)
    sources = (Path(__file__), GAIN, BUSES, line.MAPPINGS['q3'],
               HERE / 'joint_mask04_12a_buffered_line.py',
               HERE / 'joint_mask04_12a_extended_shift.py',
               HERE / 'joint_mask04_12a_fixed_gain_phase.py',
               HERE / 'joint_mask04_tx_12a_delayed_latch.py',
               HERE / 'joint_mask04_buffered_serial_handoff.py',
               HERE / 'photo_joint_line_filter_screen.py',
               HERE / 'reference_modem.py',
               HERE / 'zero_run_detector.py',
               HERE.parent / 'assumed/execute.py',
               *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='frozen-analog line comparison of held-12A and shared-127 DAC latch topologies',
                  fixture=dict(payloads={selector: [f'{value:02X}' for value in payload]
                                         for selector, payload in PAYLOADS.items()},
                               sampled_y_site='12A versus following 127',
                               offered_line_bytes='generated by established scrambler model, then clocked into the real-PROM DSC emulator',
                               sample_divisor=DIVISOR, samples=SAMPLES,
                               filter_q=0.5, shift=6, levels=LEVELS,
                               gain_source=GAIN.name,
                               candidate_dac_buses=len(buses)),
                  cases=rows,
                  limitations=[
                      'The two data and clock topologies are explicit hypotheses; this run does not measure DAC08 pins or the analog line.',
                      'The fixed gain and Q=0.5 line stage come from earlier zero-run calibration; the known-carrier decoder is external to the DSC.',
                      'A reference-decoder score alone cannot identify the actual 74LS273/74LS373 wiring.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
