"""Test a controller frame bit as the candidate A2 DAC hold-latch enable."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from main_loop_timer1_segment2 import CORE, HERE, ROM, ROOT, compile_probe, generated_source

DAC = HERE / 'results/joint-mask04-tx-prom-edge.json'
STATES = ('A1', 'A2', 'A3', 'A4')


def held_frames(rows):
    held = None
    observed = {state: [] for state in STATES}
    for row in rows:
        if row['tx']:
            if len(row['tx']) != 4:
                raise ValueError(('incomplete CD4094 frame', row))
            held = row['tx']
        state = f"{row['state']:02X}"
        if state in observed:
            if held is None:
                raise ValueError(('no held frame', state))
            observed[state].append(tuple(held))
    if any(not values for values in observed.values()):
        raise ValueError('controller state missing')
    candidates = [(byte, bit) for byte in range(4) for bit in range(8)
                  if all(all(((frame[byte] >> bit) & 1) == int(state != 'A2')
                             for frame in observed[state]) for state in STATES)]
    return observed, candidates


def dac_screen():
    prior = json.loads(DAC.read_text())
    cases = []
    for case in prior['cases']:
        for bus in case['bus_cases']:
            for phase, screen in bus['a2_gate_screen'].items():
                pass_through = screen['pass_through']
                hold = screen['hold_last_a1_code']
                if (pass_through['late_a2_to_tone_rms'] < 0.9 or
                        hold['late_a2_to_tone_rms'] >= 0.001 or
                        pass_through['data_errors'] or hold['data_errors']):
                    raise ValueError(('saved joint-map DAC screen changed',
                                      case['selector'], bus['bus_index'], phase))
                cases.append(dict(selector=case['selector'],
                                  bus_index=bus['bus_index'], phase=phase,
                                  pass_through_a2_to_a1_rms=pass_through['late_a2_to_tone_rms'],
                                  hold_a2_to_a1_rms=hold['late_a2_to_tone_rms'],
                                  hold_code=hold['a2_code'],
                                  data_errors_after_hold=hold['data_errors'],
                                  data_decisions=hold['data_decisions']))
    if len(cases) != 24:
        raise ValueError(('expected 2 selectors × 6 buses × 2 latch phases',
                          len(cases)))
    return cases


def run(out=HERE / 'results/controller-a2-latch-gate.json'):
    source, _ = generated_source()
    controller = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(source, Path(temporary), True)
        for selector in (0x40, 0x60):
            execution = json.loads(subprocess.run(
                [str(exe), str(ROM), str(selector), '10000', '1'],
                capture_output=True, text=True, check=True).stdout)
            if execution['errors'] or execution['completed'] != len(execution['iterations']):
                raise ValueError(('controller execution failed', selector))
            observed, candidates = held_frames(execution['iterations'])
            if candidates != [(2, 0)]:
                raise ValueError(('A2 latch-enable bit changed', selector, candidates))
            controller.append(dict(selector=f'{selector:02X}',
                                   iterations={state: len(values)
                                               for state, values in observed.items()},
                                   held_frames={state: sorted(' '.join(f'{v:02X}' for v in frame)
                                                              for frame in set(values))
                                                for state, values in observed.items()},
                                   active_high_A1_A3_A4_low_A2_frame_bits=candidates))
    dac = dac_screen()
    report = dict(
        status='The third CD4094 frame byte bit 0 is the unique observed active-high A1/A3/A4, low-A2 bit in both uninterrupted controller runs; a 74LS373 latch-enable hypothesis matches the saved DAC hold/silence screen.',
        fixture=dict(controller='unchanged 8031 ROM under Timer1 harness',
                     ram15='held positive at PC1000; source untraced',
                     synthetic_receive_and_status='same as interrupt-paced controller run',
                     held_frame='last completed four-byte CD4094 send persists across no-send iterations',
                     latch_hypothesis='third-frame-byte bit 0 to SN74LS373 C/LE pin 11; OC pin 1 low; high transparent, low holds last code',
                     dac_evidence='saved real-PROM mask-04 joint-map DAC capture, six photo-compatible buses, two U10 D2 latch phases, assumed 1950 Hz Q=1 bandpass'),
        controller_cases=controller,
        saved_dac_hold_cases=dac,
        summary=dict(dac_cases=len(dac),
                     pass_through_a2_to_a1_rms_range=[min(row['pass_through_a2_to_a1_rms'] for row in dac),
                                                       max(row['pass_through_a2_to_a1_rms'] for row in dac)],
                     hold_a2_to_a1_rms_range=[min(row['hold_a2_to_a1_rms'] for row in dac),
                                               max(row['hold_a2_to_a1_rms'] for row in dac)],
                     total_post_hold_data_errors=sum(row['data_errors_after_hold'] for row in dac),
                     total_post_hold_data_decisions=sum(row['data_decisions'] for row in dac)),
        limitations=[
            'A controller frame bit and a photographed 74LS373 latch are identified, but their physical connection and data-bus route are untraced.',
            'The DAC hold metrics reuse an earlier real-PROM run and an assumed analog bandpass; this script does not re-execute the DSC.',
            'The controller and DSC were not co-simulated on a shared clock; state-to-sample alignment remains a hypothesis.',
            'The 74LS273 clock, DAC08 input bus, output filter and line route are still unverified, so C2 remains open.'],
        source_sha256={str(path.relative_to(ROOT)):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in [Path(__file__), HERE / 'main_loop_timer1_segment2.py',
                                    HERE / 'main_loop_probe.c', DAC, ROM,
                                    *(CORE / name for name in
                                      ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print([(row['selector'], row['iterations'],
            row['active_high_A1_A3_A4_low_A2_frame_bits'])
           for row in report['controller_cases']])
    print(report['summary'])
