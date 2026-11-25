"""Run the joint-map transmitter through a controller-duration A2 latch hold."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_four_row_retention_tx import (HERE, candidate, fixture,
                                         hold_candidate, mapped,
                                         mapping_with_upper_source,
                                         MAPPINGS, split_scenario)
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import BUSES, bandpass
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            TONE_STEP, TONE_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_tx_divided_prom_clock import capture
from reference_modem import rms

TIMING = HERE / 'results/controller-a2-latch-gate-timing.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
A2_SYMBOLS = 74
SAMPLES_PER_SYMBOL = 8
CONTROLLER_TICKS_PER_DAC_SAMPLE = 104


def replay(mapping, base, tx_case, gate_case, buses):
    selector = tx_case['selector']
    segment2 = segment2_from_txd(tx_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (A2_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    total_symbols = TONE_SYMBOLS + A2_SYMBOLS + len(symbols)
    sample_count = total_symbols * SAMPLES_PER_SYMBOL
    tone_end = TONE_SYMBOLS * SAMPLES_PER_SYMBOL
    a2_end = (TONE_SYMBOLS + A2_SYMBOLS) * SAMPLES_PER_SYMBOL
    gate_ticks = gate_case['held_controller_ticks']
    gate_high_sample = tone_end + round(gate_ticks /
                                        CONTROLLER_TICKS_PER_DAC_SAMPLE)
    if not (a2_end <= gate_high_sample <= a2_end + SAMPLES_PER_SYMBOL):
        raise ValueError(('controller gate release moved beyond first A3 symbol',
                          selector, gate_high_sample, a2_end))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; mask04 controller-duration A2 latch hold'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (total_symbols * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        captured = capture(Path(temporary) / 'trace.jsonl', sample_count)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            captured['captured_samples'] != sample_count):
        raise ValueError(('full-duration mask04 PROM execution failed', selector,
                          result['completed_cycles'], cycles, result['stop'],
                          result['clean'], captured['captured_samples'], sample_count))
    bus_cases = []
    for index, bus in enumerate(buses):
        for phase in ('pre_rising', 'post_rom'):
            codes = mapped_codes(captured[phase], bus)
            pass_line = bandpass([value - 128 for value in codes], 1.0)
            pass_tone = rms(pass_line[64:tone_end])
            pass_a2 = rms(pass_line[a2_end - 32:a2_end]) / pass_tone
            for offset in (-1, 0, 1):
                release = gate_high_sample + offset
                gated = (codes[:tone_end] +
                         [codes[tone_end - 1]] * (release - tone_end) +
                         codes[release:])
                line = bandpass([value - 128 for value in gated], 1.0)
                tone = tone_summary(line[64:tone_end])
                score = decision_result([value + 128 for value in line[a2_end:]],
                                        symbols, sample_shift=6)
                bus_cases.append(dict(bus_index=index, phase=phase,
                                      release_sample_offset=offset,
                                      release_sample=release,
                                      hold_code=codes[tone_end - 1],
                                      pass_through_late_a2_to_a1_rms=round(pass_a2, 6),
                                      hold_late_a2_to_a1_rms=round(
                                          rms(line[a2_end - 32:a2_end]) /
                                          rms(line[64:tone_end]), 6),
                                      tone_peak_hz=tone['peak_hz'],
                                      data_errors=score['errors'],
                                      data_decisions=score['decisions']))
    return dict(selector=selector, cycles=cycles,
                trace_digest=result['trace_digest'],
                raw_rising_edges=captured['raw_rising_edges'],
                captured_samples=sample_count,
                a2_symbols=A2_SYMBOLS,
                a2_input_end_sample=a2_end,
                controller_gate_held_ticks=gate_ticks,
                assumed_gate_high_sample=gate_high_sample,
                a3_held_samples=gate_high_sample-a2_end,
                bus_cases=bus_cases)


def run(out=HERE / 'results/joint-mask04-a2-le-timed.json'):
    gate = json.loads(TIMING.read_text())
    txready = json.loads(TXREADY.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('DAC bus family changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        cases.append(replay(mapping, base,
                            next(row for row in txready['cases']
                                 if row['selector'] == selector),
                            next(row for row in gate['cases']
                                 if row['selector'] == selector),
                            buses))
        print('completed', selector, flush=True)
    rows = [row for case in cases for row in case['bus_cases']]
    report = dict(
        status='A real-PROM joint-map run extends A2 to the controller-derived hold duration and applies the candidate 74LS373 enable at the observed frame boundary.',
        fixture=dict(mapping='joint upper-source lower mask 04',
                     controller_selector_modes=['40', '60'],
                     a2_input_symbols=A2_SYMBOLS,
                     controller_to_dac_clock='104 controller machine ticks per DAC sample under 11.9808 MHz / 12 and 14.4 MHz / 1500 hypotheses',
                     gate='third CD4094 frame byte bit 0 to assumed 74LS373 C/LE; active-high transparent, low holds last A1 code',
                     gate_fall='aligned to first A2 sample; release rounded from observed frame-latch hold ticks',
                     release_offsets_tested=[-1, 0, 1],
                     dac='two U10 D2 latch phases and six photo-compatible DAC buses',
                     analog='assumed 1950 Hz Q=1 bandpass'),
        cases=cases,
        summary=dict(cases=len(rows),
                     tone_peaks_hz=sorted({row['tone_peak_hz'] for row in rows}),
                     pass_through_a2_rms_range=[min(row['pass_through_late_a2_to_a1_rms'] for row in rows),
                                                max(row['pass_through_late_a2_to_a1_rms'] for row in rows)],
                     hold_a2_rms_range=[min(row['hold_late_a2_to_a1_rms'] for row in rows),
                                        max(row['hold_late_a2_to_a1_rms'] for row in rows)],
                     data_error_range=[min(row['data_errors'] for row in rows),
                                       max(row['data_errors'] for row in rows)]),
        limitations=[
            'The DSC executes an extended A2 fixture, but its controller input schedule is reconstructed rather than co-simulated instruction by instruction.',
            'The A2 gate fall is aligned to an assumed sample phase; release is rounded to a DAC sample and tested at ±1 sample.',
            'CD4094-to-74LS373, latch data, DAC bus, analog filter and physical line connections remain untraced.',
            'An independent reference decoder scores the candidate waveform; this does not establish a physical line output or pass C2.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in [Path(__file__), TIMING, TXREADY, BUSES,
                                    HERE / 'joint_four_row_retention_tx.py',
                                    HERE / 'photo_tx_divided_prom_clock.py',
                                    HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
                                    *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['summary'])
