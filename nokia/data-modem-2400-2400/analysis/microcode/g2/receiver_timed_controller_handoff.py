"""Run a paced external-sync receive stream through the uninterrupted 8031 loop."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from main_loop_timer1_segment2 import CORE, HERE, ROM, ROOT
from receiver_mask04_controller_zero_handoff import HISTORY

SOURCE = HERE / 'results/receiver-mask04-controller-zero-handoff.json'
BIT_TICKS = 416
PULSES = (56, 63, 64, 65, 128)


def run(out=HERE / 'results/receiver-timed-controller-handoff.json'):
    prior = json.loads(SOURCE.read_text())
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for source_case in prior['cases']:
            expected = [int(value, 16) for value in source_case['recovered_line_bytes']]
            selector = 0x40 if source_case['polynomial_delay'] == 5 else 0x60
            offsets = []
            for pulse in PULSES:
                process = subprocess.run(
                    [str(exe), str(ROM), str(BIT_TICKS), str(pulse),
                     str(source_case['polynomial_delay']), str(HISTORY), str(selector),
                     *(str(value) for value in expected)],
                    capture_output=True, text=True, check=True)
                result = json.loads(process.stdout)
                result['pulse_before_rxc_bit'] = pulse if pulse < 128 else None
                if (result['errors'] or result['overruns'] or
                        result['completed'] != result['consumed'] or
                        any(consumer < producer for producer, consumer in
                            zip(result['completed_cycles'], result['consumed_cycles']))):
                    raise ValueError(('paced receive failed', source_case, pulse, result))
                offsets.append(result)
            aligned = offsets[2]
            if (aligned['consumed_bytes'] != expected or aligned['state'] != 0xB0 or
                    aligned['zero_octets'] != 8 or aligned['b0_cycle'] == 0 or
                    aligned['decoded_bytes'] != [0] * 8 or
                    aligned['completed'] != 8 or
                    bool(aligned['ram24'] & 2) != (selector == 0x40) or
                    max(consumer - producer for producer, consumer in
                        zip(aligned['completed_cycles'], aligned['consumed_cycles']))
                    >= 8 * BIT_TICKS or
                    any(row['state'] != 0xAF for row in
                        (offsets[0], offsets[1], offsets[3], offsets[4])) or
                    [row['zero_octets'] for row in offsets] != [5, 5, 8, 4, 0] or
                    [row['consumed'] for row in offsets] != [9, 8, 8, 7, 0] or
                    offsets[4]['completed'] != 0):
                raise ValueError(('timed controller alignment changed', source_case, offsets))
            mismatched = json.loads(subprocess.run(
                [str(exe), str(ROM), str(BIT_TICKS), '64',
                 str(source_case['polynomial_delay']), str(HISTORY),
                 str(0x60 if selector == 0x40 else 0x40),
                 *(str(value) for value in expected)],
                capture_output=True, text=True, check=True).stdout)
            if (mismatched['consumed_bytes'] != expected or
                    mismatched['state'] != 0xAF or mismatched['zero_octets'] != 0 or
                    mismatched['overruns'] or mismatched['decoded_bytes'] == [0] * 8):
                raise ValueError(('mismatched controller selector changed', source_case,
                                  mismatched))
            cases.append(dict(polynomial_delay=source_case['polynomial_delay'],
                              degrees=source_case['degrees'],
                              matching_controller_selector=f'{selector:02X}',
                              real_prom_trace_digest=source_case['real_prom_trace_digest'],
                              expected_line_bytes=source_case['recovered_line_bytes'],
                              opposite_selector_control=mismatched,
                              pulse_cases=offsets))
    paths = [Path(__file__), HERE / 'receiver_timed_controller_probe.c',
             SOURCE, HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'zero_run_detector.py', ROM,
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(
        status='A paced external-sync candidate delivers eight PROM-derived bytes to the uninterrupted 8031 AF loop without overrun; only the aligned pulse reaches B0.',
        fixture=dict(controller='unchanged 8031 ROM continuously executing main loop at 1ED3',
                     timer1='disabled; RAM15 held positive at PC1000',
                     dte_input='synthetic seven-byte 00 07 00 00 00 selector 00 frame per polling iteration; selector 40 for delay 5, 60 for delay 18',
                     serial_completion='synthetic SBUF completion after eight emulator ticks',
                     receive='8251 external SYNDET/RxC/RxRDY/data-read path modeled narrowly',
                     machine_ticks_per_bit=BIT_TICKS,
                     clock_hypothesis='11.9808 MHz / 12 / 2400 bit/s = 416 modeled 8031 machine ticks per RxC edge',
                     preamble='64 ones; first dibit supplied, remaining dibits from saved real-PROM receive traces',
                     controller_descrambler_history=f'{HISTORY:06X}',
                     pulse_indices=PULSES),
        cases=cases,
        limitations=[
            'The receive bits are reconstructed from saved real-PROM traces; this is not a simultaneous DSC/8031 execution.',
            'The first reversal dibit, RxD/RxC/SYNDET wiring and the SYNDET source are assumed.',
            'The 8251 model covers only the external-sync shift/RxRDY behavior, not the full chip.',
            'The DTE input and mode-0 SBUF completion are synthetic; Timer 1 is disabled and RAM15 is held positive.',
            'The controller loop reaches B0 under this fixture, but this does not identify the physical receive route or pass C3.'],
        source_sha256={str(path.relative_to(ROOT)):
                       hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['polynomial_delay'], case['degrees'],
              [(row['pulse_before_rxc_bit'], f"{row['state']:02X}",
                row['consumed'], row['overruns']) for row in case['pulse_cases']])
