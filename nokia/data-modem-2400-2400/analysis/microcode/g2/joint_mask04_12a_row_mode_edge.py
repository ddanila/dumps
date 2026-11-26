"""Challenge the candidate row clock and phase readout across a D3EB mode edge."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model
from joint_mask04_12a_row_clock_two_edge import COUNTER_GATE, high
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_3ed_prom_latch import GATE as ROW_GATE
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-row-mode-edge.json'
SELECTOR = '40'
EDGE = 32 * loopback.VISITS_PER_SYMBOL * 4 + 1
MODE_READS = 4 * handoff.ADC_VISITS + 1
CAPTURE_VISITS = (46, 93)


def execute_case(mapping, base, pcm, mode_values):
    samples = [127 - value for value in pcm]
    adc = [sample for index, sample in enumerate(samples)
           for _ in range(47 if index % 8 < 7 else 46)]
    scenario = loopback.configured(base, adc, 'previous', 'overflow', 1)
    scenario['io']['read']['pc_sequences'][str(0x3EB)] = mode_values
    scenario['io']['read']['evidence'] += '; assumed controller frame byte at D3EB'
    symbols = {symbol: {'visits': {str(visit): {} for visit in CAPTURE_VISITS}}
               for symbol in range(handoff.RX_SYMBOLS)}
    pc_digest = hashlib.sha256()
    mode_reads = row_visits = adc_reads = 0
    counter = None
    gate_edges = [0, 0]
    prior = None
    with tempfile.TemporaryDirectory() as temporary:
        result = loopback.execute(mapping, scenario, handoff.RX_CYCLES,
                                  mode='integrated', out=temporary,
                                  trace_limit=handoff.RX_CYCLES)
        if (not result['clean'] or result['completed_cycles'] != handoff.RX_CYCLES or
                result['address_counts'].get(0x3EB) != MODE_READS):
            raise ValueError('mode-edge receiver did not sustain')
        for raw in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(raw)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            levels = (high(row, ROW_GATE), high(row, COUNTER_GATE))
            if pc == 0x3EB:
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != mode_values[mode_reads]):
                    raise ValueError(('mode read changed', mode_reads))
                mode_reads += 1
            if pc == 0x3F8:
                if row['external_read']['value'] != adc[adc_reads]:
                    raise ValueError(('ADC read changed', adc_reads))
                symbol, visit = divmod(adc_reads, loopback.VISITS_PER_SYMBOL)
                if visit in CAPTURE_VISITS:
                    symbols[symbol]['visits'][str(visit)]['y3f8'] = row['alu']['y']
                adc_reads += 1
            if levels[0]:
                if counter is None:
                    counter = 0
                if counter != row_visits % 4:
                    raise ValueError(('row phase drift', row_visits))
                symbol, visit = divmod(row_visits // 4, loopback.VISITS_PER_SYMBOL)
                if visit in CAPTURE_VISITS and counter == 0:
                    symbols[symbol]['visits'][str(visit)]['row0'] = row['alu']['y']
                row_visits += 1
            if prior is not None:
                old_row, old_levels = prior
                for index in range(2):
                    if old_levels[index] and not levels[index]:
                        gate_edges[index] += 1
                        expected = ((0x3ED, 0x3EA) if index == 0 else
                                    (0x3EA, 0x3EB))
                        if (old_row['pc'], pc) != expected:
                            raise ValueError(('gate edge site changed', index))
                        if index == 1 and counter is not None:
                            counter = (counter + 1) & 3
            prior = row, levels
    if (mode_reads != MODE_READS or adc_reads != handoff.ADC_VISITS or
            row_visits != 4 * handoff.ADC_VISITS or
            gate_edges != [row_visits, row_visits + 1] or
            any(any(set(symbols[s]['visits'][str(v)]) != {'y3f8', 'row0'}
                        for v in CAPTURE_VISITS)
                for s in range(handoff.RX_SYMBOLS))):
        raise ValueError(('capture incomplete', mode_reads, adc_reads, gate_edges))
    return result, pc_digest.hexdigest(), symbols, gate_edges


def decisions(symbols, covers, inverse):
    phases = []
    for symbol in range(handoff.RX_SYMBOLS):
        first = symbols[symbol]['visits']['46']['y3f8']
        second = symbols[symbol]['visits']['93']['y3f8']
        row0 = symbols[symbol]['visits']['46']['row0']
        state = ((first >> 5) & 7) | (((second >> 7) & 1) << 3)
        state |= (((second >> 4) & 1) << 4) | (((second >> 6) & 1) << 5)
        state |= (row0 & 1) << 6
        phases.append(phase(state, covers))
    return [inverse[(after - before) & 3]
            for before, after in zip(phases, phases[1:])]


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    old = next(case for case in source['cases'] if case['selector'] == SELECTOR)
    model = json.loads(LOGIC.read_text())
    covers = covers_from_model(model)
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    fixed = json.loads(FIXED.read_text())
    gain = next(bus for bus in next(case for case in fixed['cases']
                    if case['selector'] == SELECTOR)['bus_cases']
                if bus['bus_index'] == 0)['gain']
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    payload = tuple(int(value, 16) for value in old['payload'])
    tx, raw, expected = line.transmitter(
        capturing_execute((frozen.PHASE_VISIT, 112)), mapping, base,
        line_octets(payload, 5))
    if (tx['trace_digest'] != old['tx_trace_digest'] or
            hashlib.sha256(bytes(raw)).hexdigest() != old['raw_sha256'] or
            expected != old['expected_dibits']):
        raise ValueError('transmitter changed')
    codes = mapped_codes(raw, holdout.BUSES[0])
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], 0.5)
    selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
    pcm = [max(-127, min(127, round(value * gain))) for value in selected]
    if hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != old['pcm_sha256']:
        raise ValueError('line PCM changed')
    mode_cases = {
        'held_81': [0x81] * MODE_READS,
        'edge_81_A1': [0x81] * EDGE + [0xA1] * (MODE_READS - EDGE),
    }
    rows = []
    for name, values in mode_cases.items():
        rx, pc_digest, symbols, gate_edges = execute_case(mapping, base, pcm, values)
        decoded = decisions(symbols, covers, inverse)
        wrong = [index for index, (got, want) in enumerate(
            zip(decoded, expected[1:]), 1) if got != want]
        rows.append(dict(mode=name, rx_trace_digest=rx['trace_digest'],
                         pc_digest=pc_digest, gate_edges=gate_edges,
                         wrong_indices=wrong,
                         capture_sha256=hashlib.sha256(bytes(
                             value for symbol in range(handoff.RX_SYMBOLS)
                             for visit in CAPTURE_VISITS
                             for value in (symbols[symbol]['visits'][str(visit)]['row0'],
                                           symbols[symbol]['visits'][str(visit)]['y3f8']))).hexdigest(),
                         states=[symbols[s] for s in range(handoff.RX_SYMBOLS)]))
        print('mode edge', name, len(wrong), flush=True)
    if rows[0]['pc_digest'] != rows[1]['pc_digest']:
        raise ValueError('mode transition changed PC path')
    paths = (Path(__file__), SOURCE, LOGIC, FIXED,
             HERE / 'joint_mask04_12a_row_clock_two_edge.py')
    report = dict(experiment='held versus edge controller-frame D3EB mode on full receive phase stream',
                  fixture=dict(selector=SELECTOR, phase_offset=112,
                               mode_edge_read=EDGE, mode_reads=MODE_READS,
                               mode_route='assumed controller frame byte to D3EB',
                               row_clock='two separated PROM edges and seeded modulo-four counter',
                               phase_gates='frozen 22-state model'),
                  cases=rows,
                  limitations=[
                      'The controller frame-to-D3EB route is a hypothesis; U24 reset, gates and latch nets are not traced.',
                      'The counter remains free-running across the mode edge; an externally triggered reset is not executed here.',
                      'The phase gates and USART serializer are external readouts, not identified DSC instructions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
