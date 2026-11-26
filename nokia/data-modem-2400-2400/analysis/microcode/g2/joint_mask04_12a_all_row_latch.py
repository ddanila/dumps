"""Check all four executed 3ED rows in one fresh 12A receiver stream."""

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
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json'
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-all-row-latch.json'
SELECTOR, DELAY, LEVEL = '40', 5, 0.75
PAYLOAD = (0x62, 0xE5, 0x19, 0xA7, 0xD0, 0x3B, 0x8F, 0x54)
VISITS = (46, 47, 93, 94)


def capture_rows(mapping, base, pcm):
    samples = [127 - value for value in pcm]
    adc = [sample for index, sample in enumerate(samples)
           for _ in range(47 if index % 8 < 7 else 46)]
    if len(adc) != handoff.ADC_VISITS:
        raise ValueError('receive ADC visit count changed')
    scenario = loopback.configured(base, adc, 'previous', 'overflow', 1)
    rows = {}
    adc_visit = row_visit = 0
    with tempfile.TemporaryDirectory() as temp:
        result = loopback.execute(mapping, scenario, handoff.RX_CYCLES,
                                  mode='integrated', out=temp,
                                  trace_limit=handoff.RX_CYCLES)
        if (not result['clean'] or result['completed_cycles'] != handoff.RX_CYCLES or
                result['read_sequence_visits'].get(0x3F8) != handoff.ADC_VISITS or
                result['address_counts'].get(0x3ED) != 4 * handoff.ADC_VISITS):
            raise ValueError('real-PROM receive loop stopped')
        for raw in (Path(temp) / 'trace.jsonl').open():
            item = json.loads(raw)
            if item['pc'] == 0x3F8:
                if item['external_read']['value'] != adc[adc_visit]:
                    raise ValueError('executed ADC byte changed')
                symbol, visit = divmod(adc_visit, loopback.VISITS_PER_SYMBOL)
                if visit in VISITS:
                    rows.setdefault((symbol, visit), {})['y3f8'] = item['alu']['y']
                adc_visit += 1
            elif item['pc'] == 0x3ED:
                visit_index, row_index = divmod(row_visit, 4)
                symbol, visit = divmod(visit_index, loopback.VISITS_PER_SYMBOL)
                if visit in VISITS:
                    rows.setdefault((symbol, visit), {})[f'row{row_index}'] = item['alu']['y']
                row_visit += 1
    if (adc_visit != handoff.ADC_VISITS or row_visit != 4 * handoff.ADC_VISITS or
            len(rows) != handoff.RX_SYMBOLS * len(VISITS) or
            any(set(value) != {'y3f8', 'row0', 'row1', 'row2', 'row3'}
                for value in rows.values())):
        raise ValueError('all-row capture incomplete')
    return result, adc, rows


def decisions(rows, row_index, covers, inverse):
    phases = []
    for symbol in range(handoff.RX_SYMBOLS):
        first = rows[(symbol, 46)]['y3f8']
        second = rows[(symbol, 93)]['y3f8']
        row = rows[(symbol, 46)][f'row{row_index}']
        state = ((first >> 5) & 7) | (((second >> 7) & 1) << 3)
        state |= (((second >> 4) & 1) << 4) | (((second >> 6) & 1) << 5)
        state |= (row & 1) << 6
        phases.append(phase(state, covers))
    return [inverse[(b - a) & 3] for a, b in zip(phases, phases[1:])]


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    old = next(c for c in prior['cases'] if c['selector'] == SELECTOR and
               c['level'] == LEVEL)
    fixed = json.loads(FIXED.read_text())
    gain = next(b for b in next(c for c in fixed['cases']
                               if c['selector'] == SELECTOR)['bus_cases']
                if b['bus_index'] == 0)['gain']
    model = json.loads(LOGIC.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in model['phase_bits']]
    inverse = {step: dibit for dibit, step in enumerate(model['fixture']['phase_convention'])}
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    offered = line_octets(PAYLOAD, DELAY)
    tx, raw, expected = line.transmitter(
        capturing_execute((frozen.PHASE_VISIT, 88)), mapping, base, offered)
    codes = mapped_codes(raw, holdout.BUSES[0])
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], 0.5)
    selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
    pcm = [max(-127, min(127, round(value * gain * LEVEL))) for value in selected]
    if (tx['trace_digest'] != old['tx_trace_digest'] or
            hashlib.sha256(bytes(raw)).hexdigest() != old['raw_sha256'] or
            hashlib.sha256(bytes(v + 127 for v in pcm)).hexdigest() != old['pcm_sha256'] or
            expected != old['expected_dibits'] or
            list(receive(pcm)) != expected[1:]):
        raise ValueError('transmitter or reference line differs from prior run')
    rx, adc, rows = capture_rows(mapping, base, pcm)
    if (rx['trace_digest'] != old['rx_trace_digest'] or
            hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256'] or
            any(rows[(symbol, visit)]['row0'] != old['multi_visit_symbols'][symbol]
                ['visits'][str(visit)]['row0'] or
                rows[(symbol, visit)]['row3'] != old['multi_visit_symbols'][symbol]
                ['visits'][str(visit)]['row3'] for symbol in range(handoff.RX_SYMBOLS)
                for visit in VISITS)):
        raise ValueError('new all-row trace differs from earlier PROM capture')
    scores = {}
    for index in range(4):
        decoded = decisions(rows, index, covers, inverse)
        wrong = [symbol for symbol, (got, want) in enumerate(zip(decoded, expected[1:]), 1)
                 if got != want]
        scores[f'row{index}'] = dict(wrong_indices=wrong,
                                    bit0_counts=dict(Counter(rows[(symbol, 46)]
                                                             [f'row{index}'] & 1
                                                             for symbol in range(handoff.RX_SYMBOLS))))
    if scores['row0']['wrong_indices'] or not scores['row3']['wrong_indices']:
        raise ValueError('row-qualified control changed')
    if any(rows[(symbol, visit)]['row1'] or rows[(symbol, visit)]['row2']
           for symbol in range(handoff.RX_SYMBOLS) for visit in VISITS):
        raise ValueError('intermediate row zero result changed')
    paths = (Path(__file__), PRIOR, LOGIC, FIXED,
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'joint_mask04_12a_row0_boolean.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='all four executed 3ED rows at receiver capture visits',
                  fixture=dict(selector=SELECTOR, level=LEVEL,
                               payload=[f'{v:02X}' for v in PAYLOAD],
                               phase_offset=88, captured_visits=VISITS,
                               row_clock='candidate raw 3ED edge, with or without row-0 qualifier'),
                  tx_trace_digest=tx['trace_digest'], rx_trace_digest=rx['trace_digest'],
                  adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                  per_row=scores,
                  every_row_latch_final='row3',
                  every_row_latch_wrong_indices=scores['row3']['wrong_indices'],
                  sample_rows=[dict(symbol=symbol, visit=visit,
                                    **rows[(symbol, visit)])
                               for symbol in range(handoff.RX_SYMBOLS) for visit in VISITS],
                  limitations=[
                      'This is one real-PROM call-side low-gain fixture; other selectors, levels and offsets are not all-row captures.',
                      'Raw 3ED row visits are executed ALU outputs, not proven U12 D pins or clock edges.',
                      'The row-0 qualifier, storage and USART connection remain circuit assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('all-row', {key: len(value['wrong_indices']) for key, value in scores.items()}, flush=True)
    return report


if __name__ == '__main__':
    run()
