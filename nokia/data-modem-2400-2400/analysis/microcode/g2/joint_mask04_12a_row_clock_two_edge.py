"""Check separate raw-PROM capture and counter edges on full receive traces."""

import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_3ed_prom_latch import GATE as ROW_GATE
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
ALL_ROWS = HERE / 'results/joint-mask04-12a-all-row-phase112.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-row-clock-two-edge.json'
COUNTER_GATE = ((1, 7, 1), (2, 0, 1), (3, 6, 1))  # Reached-loop 3EA decode.


def high(row, gate):
    return all(((row['raw'][chip] >> bit) & 1) == value
               for chip, bit, value in gate)


def capture(mapping, base, pcm):
    samples = [127 - value for value in pcm]
    adc = [sample for index, sample in enumerate(samples)
           for _ in range(47 if index % 8 < 7 else 46)]
    if len(adc) != handoff.ADC_VISITS:
        raise ValueError('ADC visit count changed')
    scenario = loopback.configured(base, adc, 'previous', 'overflow', 1)
    high_sites = [Counter(), Counter()]
    falling = [Counter(), Counter()]
    captured = []
    counter = None  # Assumed row-0 phase is established before first 3ED.
    row_visits = 0
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = loopback.execute(mapping, scenario, handoff.RX_CYCLES,
                                  mode='integrated', out=temporary,
                                  trace_limit=handoff.RX_CYCLES)
        if (not result['clean'] or result['completed_cycles'] != handoff.RX_CYCLES or
                result['address_counts'].get(0x3ED) != 4 * handoff.ADC_VISITS):
            raise ValueError('full real-PROM receiver did not sustain')
        for raw in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(raw)
            levels = (high(row, ROW_GATE), high(row, COUNTER_GATE))
            for index, level in enumerate(levels):
                if level:
                    high_sites[index][row['pc']] += 1
            if all(levels):
                raise ValueError('capture and counter gates overlap')
            if levels[0]:
                if counter is None:
                    counter = 0
                if counter != row_visits % 4:
                    raise ValueError(('counter row phase drift', row_visits))
                row_visits += 1
            if previous is not None:
                before, prior_levels = previous
                for index in range(2):
                    if prior_levels[index] and not levels[index]:
                        falling[index][(before['pc'], row['pc'])] += 1
                        if index == 0 and counter == 0:
                            captured.append(before['alu']['y'])
                        if index == 1 and counter is not None:
                            counter = (counter + 1) & 3
            previous = row, levels
    if (high_sites[0] != {0x3ED: 4 * handoff.ADC_VISITS} or
            high_sites[1] != {0x3EA: 4 * handoff.ADC_VISITS + 1} or
            falling[0] != {(0x3ED, 0x3EA): 4 * handoff.ADC_VISITS} or
            falling[1] != {(0x3EA, 0x3EB): 4 * handoff.ADC_VISITS + 1} or
            row_visits != 4 * handoff.ADC_VISITS or
            len(captured) != handoff.ADC_VISITS):
        raise ValueError(('gate cadence changed', high_sites, falling,
                          row_visits, len(captured)))
    return result, adc, captured, high_sites, falling


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    old_rows = json.loads(ALL_ROWS.read_text())
    fixed = json.loads(FIXED.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for old in source['cases']:
        selector = old['selector']
        delay = 5 if selector == '40' else 18
        payload = tuple(int(value, 16) for value in old['payload'])
        tx, raw, expected = line.transmitter(
            capturing_execute((frozen.PHASE_VISIT, 112)), mapping, base,
            line_octets(payload, delay))
        if (tx['trace_digest'] != old['tx_trace_digest'] or
                hashlib.sha256(bytes(raw)).hexdigest() != old['raw_sha256'] or
                expected != old['expected_dibits']):
            raise ValueError(('transmitter changed', selector))
        gain = next(bus for bus in next(case for case in fixed['cases']
                        if case['selector'] == selector)['bus_cases']
                    if bus['bus_index'] == 0)['gain']
        codes = mapped_codes(raw, holdout.BUSES[0])
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        wave = bandpass([value - 128 for value in gated], 0.5)
        selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
        pcm = [max(-127, min(127, round(value * gain))) for value in selected]
        if hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != old['pcm_sha256']:
            raise ValueError(('line PCM changed', selector))
        rx, adc, captured, sites, edges = capture(mapping, base, pcm)
        if (rx['trace_digest'] != old['rx_trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
            raise ValueError(('receiver trace changed', selector))
        prior = next(case for case in old_rows['cases'] if case['selector'] == selector)
        for item in prior['sample_rows']:
            visit = item['symbol'] * loopback.VISITS_PER_SYMBOL + item['visit']
            if captured[visit] != item['row0']:
                raise ValueError(('selected row-0 capture changed', selector, visit))
        cases.append(dict(selector=selector,
                          rx_trace_digest=rx['trace_digest'],
                          selected_row0_sha256=hashlib.sha256(bytes(captured)).hexdigest(),
                          selected_visits=len(captured),
                          high_sites=[{f'{pc:03X}': count for pc, count in s.items()}
                                      for s in sites],
                          nand_rising_edges=[{f'{a:03X}->{b:03X}': count
                                              for (a, b), count in e.items()}
                                             for e in edges]))
        print('two-edge', selector, len(captured), flush=True)
    paths = (Path(__file__), SOURCE, ALL_ROWS, FIXED,
             HERE / 'receiver_mask04_3ed_prom_latch.py')
    report = dict(experiment='two separated PROM edges for candidate row-0 U12 capture and U24 increment',
                  fixture=dict(capture_decode=ROW_GATE, counter_decode=COUNTER_GATE,
                               capture_edge='3ED->3EA',
                               increment_edge='3EA->3EB',
                               assumed_initial_counter='row 0 before first 3ED'),
                  cases=cases,
                  limitations=[
                      'Raw PROM bytes and executed PC sequence prove candidate logical edge timing only; gates and U24/U12 wires are untraced.',
                      'U24 row phase is assumed at entry; this run does not establish its physical reset source.',
                      'Propagation delays, clock pulse widths and setup/hold times are not measured.',
                      'The DAC, analog and ADC route remains the same labelled line scenario.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
