"""Screen literal controller-frame lanes as held D127 phase-step sources."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_clock_alias import SAMPLES, projected_b5
from photo_127_liveness import ROM, check_loop, run_case
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS


def reverse_bits(value):
    return int(f'{value:08b}'[::-1], 2)


def run(out=HERE / 'results/photo-127-controller-frame-steps.json'):
    # These frames were emitted by the unchanged 8031 ROM in the fixed
    # state/flags fixture in results/controller-frames.json.
    frames = {'A0': bytes.fromhex('80 02 88 7A'),
              'A1': bytes.fromhex('80 02 81 7A'),
              'A2': bytes.fromhex('80 02 88 7A')}
    controller = json.loads((HERE / 'results/controller-frames.json').read_text())
    for state, frame in frames.items():
        if next(row for row in controller['rows'] if row['state'] == state)['wire'] != frame.hex(' ').upper():
            raise ValueError(f'controller frame changed for {state}')

    candidate_report = json.loads((HERE / 'results/photo-127-fast-step-candidates.json').read_text())
    candidates = {}
    for row in candidate_report['integer_ratio_candidates']:
        key = (row['microinstruction_divisor'], row['target_hz'])
        candidates.setdefault(key, set()).add(int(row['candidate_d127'], 16))

    frame_rows = []
    for state, frame in frames.items():
        lanes = []
        for lane, value in enumerate(frame):
            reverse = reverse_bits(value)
            variants = {'literal': value, 'inverted': value ^ 255,
                        'bit_reversed': reverse, 'reversed_inverted': reverse ^ 255}
            matches = [{'transform': name, 'divisor': divisor, 'target_hz': target}
                       for name, transformed in variants.items()
                       for (divisor, target), valid in candidates.items()
                       if transformed in valid]
            lanes.append(dict(lane=lane, byte=f'{value:02X}',
                              transforms={name: f'{v:02X}' for name, v in variants.items()},
                              exact_step_matches=matches))
        frame_rows.append(dict(state=state, frame=frame.hex(' ').upper(), lanes=lanes))

    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    executed = []
    for value in sorted({value for frame in frames.values() for value in frame}):
        _, result, trace = run_case(mapping, base, value, 256)
        reads, _ = check_loop(trace, rom, value, 256)
        if not result['clean'] or not reads:
            raise ValueError(f'incomplete frame-byte run {value:02X}')
        first_phase = (3 + value) & 255
        gated = []
        for divisor in (1, 3):
            visits_per_sample = 375 // divisor
            if len(reads) != 740:
                gated.append(dict(divisor=divisor,
                                  effective_phase_step=(value * visits_per_sample) & 255,
                                  projected_samples=None,
                                  reason='executed PC129 loop exits; the checked recurrence cannot be projected as a sustained loop'))
                continue
            projected = projected_b5(rom, value,
                                     (sample * visits_per_sample
                                      for sample in range(1, SAMPLES + 1)))
            gated.append(dict(divisor=divisor,
                              effective_phase_step=(value * visits_per_sample) & 255,
                              projected_samples=SAMPLES,
                              b5_ones=sum(projected),
                              spectrum_against_2100_hz=spectrum(projected, 2100),
                              first_32_b5=''.join(map(str, projected[:32]))))
        executed.append(dict(d127=f'{value:02X}', pc129_reads=len(reads),
                             loop_sustained_for_3000_instructions=len(reads) == 740,
                             first_rom_address=f'{256 + first_phase:03X}',
                             trace_digest=result['trace_digest'], gated=gated))

    by_value = {row['d127']: row for row in executed}
    if (by_value['81']['pc129_reads'] != 125 or
            any(by_value[value]['pc129_reads'] != 740 for value in ('02', '7A', '80', '88')) or
            next(row for row in by_value['88']['gated'] if row['divisor'] == 1)
            ['spectrum_against_2100_hz']['peak_hz'] != 2100):
        raise ValueError('controller-frame lane screen changed')

    paths = [Path(__file__), HERE / 'results/controller-frames.json',
             HERE / 'results/photo-127-fast-step-candidates.json', ROM,
             HERE / 'photo_127_liveness.py', HERE / 'photo_127_clock_alias.py',
             HERE / 'photo_127_fast_step_candidates.py',
             HERE / 'photo_127_tone_probe.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='screened literal controller-frame lanes as held D127 sources',
                  fixture=dict(controller_states=list(frames), mapping='q3',
                               d127_source='one held frame byte, hypothetical',
                               output_route='upper-bank PC129 Y7 to DAC08 B5, hypothetical',
                               oscillator_divisors=[1, 3], sample_hz=9600),
                  frames=frame_rows, executed_literal_bytes=executed,
                  limitations=[
                      'A0/A1/A2 frames use a fixed controller flag/payload fixture, not a complete physical call.',
                      'The serial frame destination, CD4094 byte order, D127 connection, clock and DAC route are untraced.',
                      'Exact step matching tests a fixed D127 byte and uniform 9600 Hz gate; other logic or timing can map the frame to a tone.',
                      'The 640 gated B5 samples project beyond the 740 executed PC129 reads using their checked recurrence.',
                      'Executing each literal byte checks the microcode recurrence, not physical selection of that byte.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['frames']:
        print(row['state'], row['frame'],
              [(lane['lane'], lane['exact_step_matches']) for lane in row['lanes']
               if lane['exact_step_matches']])
