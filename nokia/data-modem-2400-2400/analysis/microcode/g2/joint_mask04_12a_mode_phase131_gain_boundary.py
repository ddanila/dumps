"""Probe the phase-131 gain boundary on both sides of first PCM clipping."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_buffered_line as line
from joint_mask04_12a_mode_phase131_adc_range import pcm_for
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_row_mode_edge import EDGE, MODE_READS, execute_case
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model
from photo_u15_u19_u21_phase_route import circuit
from reference_modem import receive

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RANGE = RESULTS / 'joint-mask04-12a-mode-phase131-adc-range.json'
BASELINE = RESULTS / 'joint-mask04-12a-mode-phase131-baseline-control.json'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
OUT = RESULTS / 'joint-mask04-12a-mode-phase131-gain-boundary.json'
FACTORS = (1.15, 1.175)


def run(out=OUT):
    spectrum = json.loads(RANGE.read_text())
    baseline = json.loads(BASELINE.read_text())
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    covers = covers_from_model(model)
    known = {int(code, 16) for code in model['trained_state_phase']}
    known.update((0x3D, 0x4C, 0x02, 0x6E))
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    mode_values = [0x81] * EDGE + [0xA1] * (MODE_READS - EDGE)
    cases = []
    for factor in FACTORS:
        for wave_case, source in zip(spectrum['cases'], baseline['cases']):
            selector = wave_case['selector']
            if selector != source['selector']:
                raise ValueError('gain boundary selector changed')
            unbounded = [round(value * wave_case['calibrated_gain'] * factor)
                         for value in wave_case['selected_wave']]
            clipped = sum(abs(value) > 127 for value in unbounded)
            pcm = pcm_for(wave_case['selected_wave'],
                          wave_case['calibrated_gain'], factor)
            expected = source['expected_dibits']
            reference_wrong = [index for index, (got, want) in
                               enumerate(zip(receive(pcm), expected[1:]), 1)
                               if got != want]
            rx, pc_digest, symbols, gate_edges = execute_case(
                mapping, base, pcm, mode_values)
            captures = [symbols[index] for index in range(len(expected))]
            states = [sample_state(symbol, SELECTED) for symbol in captures]
            package_phases = [circuit(state, 1) for state in states]
            old_phases = [phase(state, covers) for state in states]
            def wrong(phases):
                return [index for index in range(1, len(phases))
                        if inverse[(phases[index] - phases[index - 1]) & 3]
                        != expected[index]]
            if len(states) != 65 or len(expected) != 65:
                raise ValueError(('gain boundary symbol count', factor, selector))
            cases.append(dict(selector=selector, factor=factor,
                              clipped_samples=clipped,
                              unbounded_peak=max(abs(value) for value in unbounded),
                              pcm_sha256=hashlib.sha256(
                                  bytes(value + 127 for value in pcm)).hexdigest(),
                              rx_trace_digest=rx['trace_digest'],
                              pc_digest=pc_digest, gate_edges=gate_edges,
                              observed_states=[f'{value:02X}' for value in states],
                              unseen_states=sorted(f'{value:02X}' for value in
                                                   set(states) - known),
                              expected_dibits=expected,
                              reference_wrong_indices=reference_wrong,
                              old_cover_wrong_indices=wrong(old_phases),
                              package_circuit_wrong_indices=wrong(package_phases),
                              package_circuit_phases=package_phases,
                              multi_visit_symbols=captures))
            print(selector, factor, 'clip', clipped,
                  'reference', len(reference_wrong),
                  'old', len(cases[-1]['old_cover_wrong_indices']),
                  'package', len(cases[-1]['package_circuit_wrong_indices']),
                  'states', sorted(set(cases[-1]['observed_states'])), flush=True)
    paths = (Path(__file__), RANGE, BASELINE, MODEL,
             HERE / 'joint_mask04_12a_row_mode_edge.py',
             HERE / 'photo_u15_u19_u21_phase_route.py')
    report = dict(experiment='phase-131 receive gain boundary across first PCM clipping',
                  fixture=dict(factors=FACTORS, R1_offset=131,
                               same_payloads_as=BASELINE.name,
                               mode='assumed 81-to-A1 at D3EB'),
                  cases=cases,
                  limitations=[
                      'The saved real-PROM transmitted line is fixed; each receiver run executes the real PROMs under a new modeled PCM gain.',
                      'Clipping refers to the modeled PCM conversion, not a measured ADC rail on the photographed board.',
                      'The DAC, line, ADC, mode, capture, logic and serial routes remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
