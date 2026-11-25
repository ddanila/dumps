"""Screen raw PROM edges for A1-only second-loop latch timing."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from execute import execute
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_output_clock_bit_screen import CHIPS, edges

CYCLES = 3000
SITES = (0, 2, 3)
EDGE = ('18', 1, 'rising')


def run_trace(mapping, base, control, step):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [control]
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [step]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('state edge run incomplete')
    return result, trace


def run(out=HERE / 'results/photo-12c-prom-edge-latch.json'):
    frames = frames_from_reports()
    chips = {state: shift_four_bytes(frames[f'state_{state}'])
             for state in ('A0', 'A1')}
    if ([chips[state][1]['q8_to_d0'] for state in ('A0', 'A1')] !=
            [0x88, 0x81]):
        raise ValueError('state frame/control lane changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for step_chip in SITES:
        runs = {}
        for state in ('A0', 'A1'):
            control = chips[state][1]['q8_to_d0']
            step = chips[state][step_chip]['q8_to_d0']
            result, trace = run_trace(mapping, base, control, step)
            if (state == 'A1' and
                    (step & 1 or sum(row['pc'] == 0x12E for row in trace) != 613)):
                raise ValueError('A1 second-loop fixture changed')
            if state == 'A0' and any(row['pc'] == 0x12E for row in trace):
                raise ValueError('A0 entered second loop')
            runs[state] = (result, trace, control, step)
        a0, a1 = runs['A0'][1], runs['A1'][1]
        targets = {index for index, row in enumerate(a1) if row['pc'] == 0x12E}
        a0_loop = {index for index, row in enumerate(a0) if row['pc'] == 0x129}
        screened = []
        for lane, chip in enumerate(CHIPS):
            for bit in range(8):
                for rising in (0, 1):
                    e1 = set(edges(a1, lane, bit, rising))
                    if not targets <= e1:
                        continue
                    e0 = set(edges(a0, lane, bit, rising))
                    screened.append(dict(chip=chip, bit=bit,
                                         edge='rising' if rising else 'falling',
                                         a1_target_hits=len(e1 & targets),
                                         a1_other_edges=len(e1 - targets),
                                         a0_first_loop_edges=len(e0 & a0_loop),
                                         a0_other_edges=len(e0 - a0_loop)))
        isolated = [row for row in screened
                    if row['a0_first_loop_edges'] == 0 and
                       row['a1_other_edges'] <= 7]
        if [(row['chip'], row['bit'], row['edge']) for row in isolated] != [EDGE]:
            raise ValueError('unique A1-only raw-edge candidate changed')
        selected_edges = edges(a1, CHIPS.index('18'), 1, 1)
        a0_edges = edges(a0, CHIPS.index('18'), 1, 1)
        captures = [a1[index]['alu']['y'] for index in selected_edges
                    if index in targets]
        b5 = [(value >> 7) & 1 for value in captures]
        other = [dict(cycle=a1[index]['cycle'], pc=f'{a1[index]["pc"]:03X}')
                 for index in selected_edges if index not in targets]
        if (len(captures) != 613 or len(other) != 7 or
                len(a0_edges) != 6 or
                any(a0[index]['pc'] == 0x129 for index in a0_edges)):
            raise ValueError('U18 D1 edge schedule changed')
        cases.append(dict(step_chip=step_chip,
                          a0_d127=f'{runs["A0"][2]:02X}',
                          a1_d127=f'{runs["A1"][2]:02X}',
                          d12c=f'{runs["A1"][3]:02X}',
                          a1_rom_reads=len(targets),
                          a1_aligned_raw_edge_candidates=screened,
                          isolated_raw_edge=isolated[0],
                          a1_u18_d1_sustained_captures=len(captures),
                          a1_u18_d1_distinct_y_codes=len(set(captures)),
                          a1_u18_d1_first_16_y=[f'{value:02X}' for value in captures[:16]],
                          a1_photo_b5_y7_transitions=sum(a != b
                              for a, b in zip(b5, b5[1:])),
                          a1_photo_b5_y7_ones=sum(b5),
                          a1_u18_d1_extra_edges=other,
                          a0_u18_d1_edges=len(a0_edges),
                          a0_u18_d1_first_loop_edges=0,
                          trace_digests={state: runs[state][0]['trace_digest']
                                         for state in ('A0', 'A1')}))
    paths = [Path(__file__), HERE / 'photo_cd4094_order.py',
             HERE / 'photo_output_clock_bit_screen.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='A1-only raw PROM edge and hypothetical LS273 capture screen',
                  fixture=dict(mapping='q3 photo-swapped', q=0,
                               cd4094='logical chip 1 Q8→D0 at D127',
                               d12c='held other Q8→D0 chip byte',
                               bank_129_12e='upper', cycles_per_case=CYCLES,
                               latch_data='Am2901 ALU Y at raw edge',
                               latch_clock='candidate U18 D1 rising edge',
                               photo_b5_candidate='Y7→LS273 D4→Q4→DAC08 B5'),
                  cases=cases,
                  clock_rate_hypothesis=dict(oscillator_hz=14400000,
                                             loop_microinstructions=4,
                                             oscillator_periods_per_microinstruction=[1, 4],
                                             unqualified_edge_hz_range=[900000, 3600000],
                                             proposed_dac_sample_hz=9600),
                  limitations=[
                      'U18 D1 is a PROM data bit with a tentative register-address role; no wire to the DAC-side 74LS273 clock is traced.',
                      'The A0/A1 CD4094 bus, both DSP D routes, q3 mapping and ROM bank are hypotheses.',
                      'A direct edge would update at 0.9–3.6 MHz for the tested microcycle ratios, so a divider/gate or different clock is needed for a 9600 Hz DAC stream.',
                      'Y7→LS273 D4 is assumed; only Q4→DAC08 B5 is photo-suggested, and changing ALU bytes are not a measured DAC input or line waveform.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['step_chip'], case['d12c'],
              case['a1_u18_d1_sustained_captures'],
              case['a1_u18_d1_distinct_y_codes'],
              case['a0_u18_d1_first_loop_edges'])
