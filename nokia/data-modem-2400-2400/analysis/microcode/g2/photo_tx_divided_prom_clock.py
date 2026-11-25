"""Clock a candidate DAC latch from divided raw U10.D2 edges in joined runs."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_controller_path import fixture
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_i0_hold_screen import hold_candidate
from photo_joint_free_clock_sites import CYCLES_PER_SAMPLE, START_CYCLE
from photo_joint_line_filter_screen import (BUSES, JOINT, TXREADY, TONE_END,
                                            SILENCE_END, bandpass)
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SAMPLE, VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_joint_waveform_shape_screen import best_fit, reference_templates
from reference_modem import rms

LINE_FILTER = HERE / 'results/photo-joint-line-filter-screen.json'
FREE_CLOCK = HERE / 'results/photo-joint-free-clock-sites.json'
FIRST_PC = 0x127
SAMPLE_COUNT = TOTAL_SYMBOLS * 8
DIVISOR = VISITS_PER_SAMPLE


def capture(path, sample_count=SAMPLE_COUNT):
    """Counter-qualify actual 129 rises and 12A falls; capture preceding Y."""
    pre_rising = []
    post_rom = []
    first_127 = None
    rise_count = fall_count = 0
    previous_128 = previous_129 = None
    last_sample_cycle = None
    with path.open() as source:
        for line in source:
            # The joined run is a four-word loop after its startup prefix.
            # Parse only the three rows needed for both edge phases.
            if all(f'"pc": {pc}' not in line for pc in (0x127, 0x128, 0x129, 0x12A)):
                continue
            row = json.loads(line)
            pc = row['pc']
            if pc == FIRST_PC and first_127 is None:
                first_127 = row['cycle']
            if first_127 is None or row['cycle'] < START_CYCLE:
                continue
            raw_level = (row['raw'][0] >> 2) & 1
            if pc == 0x127:
                if raw_level != 0:
                    raise ValueError('U10.D2 high at loop start')
            elif pc == 0x128:
                if raw_level != 0:
                    raise ValueError('U10.D2 high before 129')
                previous_128 = row
            elif pc == 0x129:
                if (raw_level != 1 or previous_128 is None or
                        previous_128['cycle'] + 1 != row['cycle']):
                    raise ValueError('U10.D2 rising edge timing changed')
                if rise_count % DIVISOR == 0 and len(pre_rising) < sample_count:
                    pre_rising.append(previous_128['alu']['y'])
                rise_count += 1
                previous_129 = row
            elif pc == 0x12A:
                if (raw_level != 0 or previous_129 is None or
                        previous_129['cycle'] + 1 != row['cycle']):
                    raise ValueError('U10.D2 falling edge timing changed')
                if fall_count % DIVISOR == 0 and len(post_rom) < sample_count:
                    if (last_sample_cycle is not None and
                            row['cycle'] - last_sample_cycle != CYCLES_PER_SAMPLE):
                        raise ValueError('divided PROM sample clock drifted')
                    post_rom.append(previous_129['alu']['y'])
                    last_sample_cycle = row['cycle']
                fall_count += 1
    if (first_127 != START_CYCLE or rise_count != fall_count or
            len(pre_rising) != sample_count or len(post_rom) != sample_count):
        raise ValueError(('divided PROM capture incomplete', first_127,
                          rise_count, fall_count,
                          len(pre_rising), len(post_rom)))
    return dict(pre_rising=pre_rising, post_rom=post_rom,
                first_pc127_cycle=first_127,
                raw_rising_edges=rise_count, raw_falling_edges=fall_count,
                captured_samples=sample_count,
                first_capture_cycle=START_CYCLE + 3,
                final_capture_cycle=last_sample_cycle)


def line_metrics(raw, bus, symbols, templates):
    codes = mapped_codes(raw, bus)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([value - 128 for value in gated], 1.0)
    tone = tone_summary(line[64:TONE_END])
    score = decision_result([value + 128 for value in line[SILENCE_END:]],
                            symbols, sample_shift=6)
    shape_r2, shape_alignment = best_fit(
        [value + 128 for value in line[SILENCE_END:]], templates)
    return dict(tone_peak_hz=tone['peak_hz'], tone_r2_2100=tone['r2_2100'],
                data_errors=score['errors'], data_shape_r2=shape_r2,
                data_shape_alignment=shape_alignment,
                late_a2_rms=rms(line[SILENCE_END - 32:SILENCE_END]),
                late_tone_rms=rms(line[64:TONE_END]))


def replay(selector, tx_case, joint_case, free_case, filter_cases, buses, base):
    segment2 = segment2_from_txd(tx_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    scenario = hold_candidate(base)
    scenario['name'] += '; free-clock four ALU sites'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapped(MAPPINGS['q3']), scenario, cycles,
                         mode='integrated', out=temporary, trace_limit=cycles)
        captured = capture(Path(temporary) / 'trace.jsonl')
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['trace_digest'] != free_case['trace_digest'] or
            result['address_counts'].get(0x129, 0) != captured['raw_rising_edges']):
        raise ValueError(('joined real-PROM edge replay changed', selector))
    site = {row['pc']: row for row in free_case['sites']}
    for name, pc in (('pre_rising', '128'), ('post_rom', '129')):
        digest = hashlib.sha256(bytes(mapped_codes(captured[name], SELECTED))).hexdigest()
        if digest != site[pc]['sample_sha256']:
            raise ValueError(('divided edge sample differs from joined site', selector, name))
    bus_cases = []
    templates = reference_templates(symbols)
    for index, bus in enumerate(buses):
        pre = line_metrics(captured['pre_rising'], bus, symbols, templates)
        post = line_metrics(captured['post_rom'], bus, symbols, templates)
        saved = next(row for row in filter_cases
                     if row['selector'] == selector and row['bus_index'] == index
                     and row['q'] == 1.0)
        if (abs(post['tone_r2_2100'] - saved['tone_r2_2100']) > 1e-10 or
                post['data_errors'] != saved['errors_by_sample_shift'][6] or
                post['tone_peak_hz'] != saved['tone_peak_hz']):
            raise ValueError(('post-ROM line metrics differ from saved joined run',
                              selector, index))
        bus_cases.append(dict(bus_index=index, input_bit_to_dac_code_bit=bus,
                              pre_rising=pre, post_rom=post))
    return dict(selector=selector, cycles=cycles,
                trace_digest=result['trace_digest'],
                edge_counts=dict(rising=captured['raw_rising_edges'],
                                 falling=captured['raw_falling_edges']),
                captured_samples=SAMPLE_COUNT,
                first_capture_cycle=captured['first_capture_cycle'],
                final_capture_cycle=captured['final_capture_cycle'],
                selected_bus_sha256={name: hashlib.sha256(bytes(mapped_codes(
                    captured[name], SELECTED))).hexdigest()
                    for name in ('pre_rising', 'post_rom')},
                bus_cases=bus_cases)


def run(out=HERE / 'results/photo-tx-divided-prom-clock.json'):
    txready = json.loads(TXREADY.read_text())
    joined = json.loads(JOINT.read_text())
    free = json.loads(FREE_CLOCK.read_text())
    filter_report = json.loads(LINE_FILTER.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('surviving DAC bus family changed')
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        cases.append(replay(
            selector,
            next(row for row in txready['cases'] if row['selector'] == selector),
            next(row for row in joined['cases'] if row['selector'] == selector),
            next(row for row in free['cases'] if row['selector'] == selector),
            filter_report['cases'], buses, base))
        print('captured selector', selector, flush=True)
    if any(row['post_rom']['data_errors'] != 0 or
           row['post_rom']['tone_peak_hz'] != 2100
           for case in cases for row in case['bus_cases']):
        raise ValueError('post-ROM line signatures changed')
    paths = [Path(__file__), TXREADY, JOINT, FREE_CLOCK, LINE_FILTER, BUSES,
             ROM, HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_joint_free_clock_sites.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_joint_waveform_shape_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='rate-qualified U10.D2 DAC latch edge in uninterrupted real-PROM traces',
        fixture=dict(controller_selectors=('40', '60'),
                     strobe='raw U10.D2 rises at 129 and falls at 12A',
                     divisor=DIVISOR, assumed_sample_hz=9600,
                     direct_rising_phase='previous 128 Y if clock beats new ALU Y',
                     inverted_falling_phase='previous 129 Y if clock beats 12A ALU Y',
                     latch='candidate 74LS273; data bus, inverter, divider and clock wire untraced',
                     analog='assumed A2 mid-code gate and fixed 1950 Hz Q=1 bandpass'),
        cases=cases,
        limitations=[
            'A divided U10.D2 clock is a wiring/timing hypothesis, not a traced DAC clock.',
            'The six full DAC bus orders, A2 mute and analog filter are conditional models.',
            'Matching the saved joined trace and line metrics does not identify the physical line output.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'], case['edge_counts'], case['captured_samples'])
