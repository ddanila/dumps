"""Run the joint upper-source map through the full controller-driven TX trace."""

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
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_controller_path import fixture
from photo_dac_bus_permutations import matched_filter_basis, score
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
    TOTAL_SYMBOLS, segment2_from_txd,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from split_slice_probe import split_scenario

TXREADY = HERE / 'results/main-loop-usart-txready.json'
JOINED = HERE / 'results/photo-joint-tone-training-data.json'
SAMPLES_PER_SYMBOL = 8


def replay(mapping, base, rom, selector, segment2, baseline):
    target = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(target))
    if len(inputs) != TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 1:
        raise ValueError('controller-derived D127 input length changed')
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; joint upper-source full TX controller trace'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += (
            '; same diagnostic level at U8 A pin is a separate untraced hypothesis')
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        checked = inspect(Path(temporary) / 'trace.jsonl', rom, inputs,
                          [0] * TOTAL_SYMBOLS)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['address_counts'].get(0x129) != checked['pc129_visits'] or
            result['address_counts'].get(0x12E, 0)):
        raise ValueError(('full joint TX run stopped', selector))
    data_start = (TONE_SYMBOLS + SILENCE_SYMBOLS) * SAMPLES_PER_SYMBOL
    basis = matched_filter_basis(checked['samples'][data_start:])
    errors, decisions = score(basis, target, tuple(range(8)))
    prior_hash = baseline['selected_bus_sample_sha256']
    phase_after_tone = checked['symbol_end_phases'][TONE_SYMBOLS - 1]
    phase_after_silence = checked['symbol_end_phases'][TONE_SYMBOLS + SILENCE_SYMBOLS - 1]
    phase_milestones_match_prior = (
        phase_after_tone == baseline['phase_after_tone'] and
        phase_after_silence == baseline['phase_after_silence'])
    return dict(selector=selector, dsc_microinstructions=cycles,
                pc129_visits=checked['pc129_visits'],
                sample_count=len(checked['samples']),
                selected_bus_sample_sha256=checked['sample_sha256'],
                matches_prior_q3_selected_bus=(checked['sample_sha256'] == prior_hash),
                phase_after_tone=phase_after_tone,
                phase_after_silence=phase_after_silence,
                phase_milestones_match_prior=phase_milestones_match_prior,
                tone=tone_summary(checked['samples'][:TONE_SYMBOLS * SAMPLES_PER_SYMBOL]),
                data_errors=errors, data_decisions=decisions,
                a3_a4_boundary_samples=[f'{code:02X}' for code in
                                        checked['samples'][(TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * SAMPLES_PER_SYMBOL - 4:
                                                           (TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * SAMPLES_PER_SYMBOL + 4]],
                trace_digest=result['trace_digest'],
                scenario_digest=result['scenario_digest'])


def run(out=HERE / 'results/joint-upper-full-tx-replay.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    mapping = candidate(receiver, transmitter, SELECTED_MASK)
    _, base = fixture()
    rom = ROM.read_bytes()
    txready = json.loads(TXREADY.read_text())
    joined = json.loads(JOINED.read_text())
    cases = []
    for selector in ('40', '60'):
        prior = next(case for case in joined['cases'] if case['selector'] == selector)
        clock_case = next(case for case in txready['cases']
                          if case['selector'] == selector)
        segment2 = segment2_from_txd(clock_case)
        cases.append(replay(mapping, base, rom, selector, segment2, prior))
    if any(case['sample_count'] != TOTAL_SYMBOLS * SAMPLES_PER_SYMBOL or
           case['data_decisions'] != 62 or case['data_errors'] != 0 or
           case['tone']['peak_hz'] != 2100 or
           not case['matches_prior_q3_selected_bus'] or
           not case['phase_milestones_match_prior'] for case in cases):
        raise ValueError('full joint TX sample, phase or decision result changed')
    paths = [Path(__file__), HERE / 'joint_upper_source_screen.py',
             HERE / 'joint_tx_rx_mapping_screen.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'], TXREADY, JOINED, ROM,
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='full controller-derived TX stream through one split-slice map also used by sustained ADC experiment',
                  fixture=dict(mapping='joint upper-source mask 08',
                               controller_selectors=['40', '60'],
                               input='observed A1/A2 frame decode and TxRDY-paced A3/A4 TxD bytes; D127 ingress timing is hypothetical',
                               high_a='separately labelled diagnostic U8 A pin levels match U2 A pins',
                               output='hypothetical ordered Y to DAC bus with Q4/Q5 swap and free-running 9600 Hz sample phase'),
                  cases=cases,
                  limitations=[
                      'The high I0/I7 source, U8 A pins, input decoder, DAC latch and analog line connection are untraced.',
                      'An exact q3 output hash or reference-decoder score would establish only conditional signal behavior, not physical Nokia wiring.',
                      'The receiver side has no recovered dibit, echo cancellation or USART RxD proof.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(row['selector'], row['matches_prior_q3_selected_bus'],
            row['tone']['peak_hz'], row['data_errors'], row['data_decisions'])
           for row in report['cases']])
