"""Screen raw PROM output edges as clocks at transient D127 ROM sites."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from photo_127_liveness import run_case
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_output_clock_bit_screen import CHIPS, edges


def run(out=HERE / 'results/photo-127-clock-screen.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for increment in (48, 56):
        _, result, trace = run_case(mapping, base, increment, 256)
        targets = {pc: {i for i, row in enumerate(trace) if row['pc'] == pc}
                   for pc in (0x129, 0x12A)}
        if any(len(indexes) != 740 for indexes in targets.values()):
            raise ValueError('repeated D127 loop changed')
        candidate_bits = []
        for lane, chip in enumerate(CHIPS):
            for bit in range(8):
                for rising in (0, 1):
                    indexes = set(edges(trace, lane, bit, rising))
                    for pc, visits in targets.items():
                        if visits <= indexes:
                            candidate_bits.append(dict(
                                pc=f'{pc:03X}', chip=chip, bit=bit,
                                edge='rising' if rising else 'falling',
                                target_visits=len(visits),
                                total_edges=len(indexes),
                                extra_edges=len(indexes - visits)))
        cases.append(dict(increment=increment, cycles=len(trace),
                          candidates=sorted(candidate_bits,
                                            key=lambda row: (row['pc'], row['chip'],
                                                             row['bit'], row['edge'])),
                          trace_digest=result['trace_digest']))
    if cases[0]['candidates'] != cases[1]['candidates']:
        raise ValueError('direct-clock candidates depend on D127 increment')
    if [sum(row['pc'] == pc for row in cases[0]['candidates'])
        for pc in ('129', '12A')] != [11, 6]:
        raise ValueError('direct-clock candidate count changed')
    paths = [Path(__file__), HERE/'photo_127_liveness.py',
             HERE/'photo_output_clock_bit_screen.py',
             HERE/'photo_controller_path.py', HERE/'photo_i0_hold_screen.py',
             HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
             ASSUMED/'execute.py', HERE.parent/'model.py', *MAPPINGS.values()]
    report = dict(status='raw-PROM-edge timing screen, not traced LS273 clock',
                  fixture=dict(mapping='q3', initial_q=0, held_i0=1,
                               d127_values=[48, 56], selected_rom_bank=256,
                               cycles=3000, target_pcs=['129', '12A'],
                               edge_source='one raw data bit from U10/U11/U17/U18'),
                  repeated_loop_microinstructions=4,
                  rate_hypothesis=dict(oscillator_hz=14400000,
                                       oscillator_cycles_per_microinstruction=[1, 4],
                                       direct_edge_hz_range=[900000, 3600000],
                                       proposed_sample_hz=9600,
                                       oscillator_cycles_per_microinstruction_for_9600=375),
                  cases=cases,
                  limitations=[
                      'These are edge correlations in a PROM-output trace, not pin-level clock connections.',
                      'Extra edges outside the repeated quartet would also clock an unqualified latch.',
                      'A decoder, divider, hold circuit or much slower sequencer clock could change the sample schedule.',
                      'The 9600 Hz sample rate and k=1..4 microcycle divisor are hypotheses, not measured board timing.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['increment'],
              {pc: sum(row['pc'] == pc for row in case['candidates'])
               for pc in ('129', '12A')})
