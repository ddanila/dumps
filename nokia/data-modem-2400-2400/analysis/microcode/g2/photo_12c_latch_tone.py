"""Screen PC12E/PC12F transient values as photo-B5 latch candidates."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_clock_alias import SAMPLES
from photo_127_liveness import ROM, CYCLES
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS


def sample_values(rom, step, visits):
    phases = []
    selected = []
    e_values = []
    f_values = []
    for n in visits:
        phase = (1 + n * step) & 255
        value = rom[256 + phase]
        carry = int(phase >= value)
        phases.append(phase)
        selected.append(value)
        e_values.append((phase - value) & 255)
        f_values.append((phase + 1 + carry) & 255)
    return phases, selected, e_values, f_values


def run(out=HERE / 'results/photo-12c-latch-tone.json'):
    candidates = json.loads((HERE / 'results/photo-127-fast-step-candidates.json').read_text())[
        'integer_ratio_candidates']
    if len(candidates) != 8:
        raise ValueError('fast-step source changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for candidate in candidates:
        step = int(candidate['candidate_d127'], 16)
        divisor = candidate['microinstruction_divisor']
        target = candidate['target_hz']
        scenario = hold_candidate(base)
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = [0x81]
        scenario['io']['read']['pc_sequences'][str(0x12C)] = [step]
        scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                           str(0x12E): 256}
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=temporary, trace_limit=CYCLES)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        e_rows = [row for row in trace if row['pc'] == 0x12E]
        f_rows = [row for row in trace if row['pc'] == 0x12F]
        if not result['clean'] or len(e_rows) != 613 or len(f_rows) != 613:
            raise ValueError(f'PC12C={step:02X} scan changed')
        phases, selected, e_values, f_values = sample_values(rom, step,
                                                            range(1, 614))
        if (phases != [row['external_read']['address'] & 255 for row in e_rows] or
                selected != [row['external_read']['value'] for row in e_rows] or
                e_values != [row['alu']['y'] for row in e_rows] or
                f_values != [row['alu']['y'] for row in f_rows] or
                any(not row['external_read']['selected_by_alu'] for row in e_rows) or
                any(b['cycle'] - a['cycle'] != 4 for a, b in zip(e_rows, e_rows[1:]))):
            raise ValueError(f'PC12C={step:02X} phase/ROM/Y recurrence changed')
        visits_per_sample = 375 // divisor
        visits = (sample * visits_per_sample for sample in range(1, SAMPLES+1))
        phase, rom_bytes, y_e, y_f = sample_values(rom, step, visits)
        spectra = {}
        for site, values in (('12E', y_e), ('12F', y_f)):
            spectra[site] = dict(raw_y_byte=spectrum(values, target),
                                 photo_b5_y7=spectrum([(value >> 7) & 1
                                                     for value in values], target),
                                 first_16_y=values[:16])
        spectra['phase_ramp'] = spectrum(phase, target)
        spectra['rom_byte'] = spectrum(rom_bytes, target)
        if any(spectra[site]['photo_b5_y7']['peak_hz'] != target
               for site in ('12E', '12F')):
            raise ValueError(f'PC12C={step:02X} projected B5 peak changed')
        cases.append(dict(held_d12c=f'{step:02X}', divisor=divisor,
                          target_hz=target, direction=candidate['direction'],
                          executed_pc12e_reads=len(e_rows),
                          executed_pc12f_visits=len(f_rows),
                          projected_gated_samples=SAMPLES,
                          visits_per_sample=visits_per_sample,
                          spectra=spectra, trace_digest=result['trace_digest']))

    paths = [Path(__file__), ROM,
             HERE / 'results/photo-127-fast-step-candidates.json',
             HERE / 'photo_127_clock_alias.py', HERE / 'photo_127_tone_probe.py',
             HERE / 'photo_127_liveness.py', HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg',
             MAPPINGS['q3']]
    report = dict(status='PC12E/PC12F transient latch projection, not line output',
                  fixture=dict(mapping='q3', held_d127='81',
                               d12c_source='held candidate step',
                               output_route='Y7→LS273 D4→Q4→DAC08 B5, hypothetical except photographed B5←Q4 segment',
                               latch_sites=['12E', '12F'],
                               oscillator_hz=14400000, sample_hz=9600,
                               integer_microinstruction_divisors=[1, 3],
                               first_sample_alignment='visit 375/divisor'),
                  cases=cases,
                  limitations=[
                      'Only the first 613 PC12E/PC12F visits are executed per step; 640 gated samples project the checked recurrence.',
                      'The D127/D12C sources, Y7-to-D4 route, LS273 clock, full DAC byte wiring and oscillator divisor are untraced.',
                      'A B5 spectral peak and raw-Y byte ramp can occur without a sinusoidal analog carrier or controller command.',
                      'No controller data modulation, receiver/echo behavior or physical line output is shown.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['held_d12c'], row['divisor'], row['target_hz'],
              row['spectra']['12E']['photo_b5_y7']['sinusoid_r2'],
              row['spectra']['12F']['photo_b5_y7']['sinusoid_r2'])
