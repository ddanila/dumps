"""Execute the 8031's state-AF scrambled-zero octet transition."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from controller_scrambler import transform
from state_transitions import CORE, ROM

STANDARD = 'https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I%21%21PDF-E&lang=e&type=items'
HISTORY = 0x5A1234
SEQUENCES = {
    'seven_zero_octets': [0] * 7,
    'eight_zero_octets': [0] * 8,
    'seven_zero_then_one': [0] * 7 + [1],
    'eight_one_octets': [255] * 8,
    'interrupted_then_seven': [0] * 7 + [1] + [0] * 7,
    'interrupted_then_eight': [0] * 7 + [1] + [0] * 8,
}


def line_octets(values, delay):
    history = HISTORY
    result = []
    for value in values:
        history, wire = transform(history, value, delay)
        result.append(wire)
    return result


def run(out=HERE / 'results/zero-run-detector.json'):
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'zero-run-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-function',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'zero_run_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay in (5, 18):
            for label, values in SEQUENCES.items():
                offered = line_octets(values, delay)
                completed = subprocess.run(
                    [str(exe), str(ROM), str(delay), str(HISTORY),
                     *(str(value) for value in offered)],
                    capture_output=True, text=True, check=True)
                result = json.loads(completed.stdout)
                decoded = [event['decoded'] for event in result['octets']]
                counts = [event['zero_octets'] for event in result['octets']]
                expected_counts = []
                count = 0
                for value in values:
                    count = count + 1 if value == 0 else 0
                    expected_counts.append(count)
                expected_state = 0xB0 if count >= 8 else 0xAF
                assert decoded == values and counts == expected_counts
                assert all(event['status_reads'] == event['data_reads'] == 1
                           for event in result['octets'])
                assert (result['state_after'], result['zero_octets'],
                        result['errors'], result['reached_stop']) == (
                            expected_state, count, 0, True)
                assert [event['line'] for event in result['octets']] == offered
                rows.append(dict(delay=delay, sequence=label,
                                 line_bytes=[f'{value:02X}' for value in offered],
                                 decoded_bytes=[f'{value:02X}' for value in decoded],
                                 zero_octets_after_each=counts,
                                 final_state=f'{expected_state:02X}',
                                 errors=0))
    paths = [Path(__file__), HERE / 'zero_run_probe.c',
             HERE / 'state_transitions.py',
             HERE.parents[1] / 'controller_scrambler.py', ROM,
             *(CORE / name for name in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(status='executed state-AF eight-zero-octet detector after ROM descrambling',
                  standard=STANDARD,
                  standard_section='V.26 ter (11/88) 6.3.1.3; 64 received scrambled binary zeros',
                  fixture=dict(entry_receive_dispatch='08E9',
                               dispatched_handler='0A4E: 1DB8 USART-01 read, 05A3 descrambler, 1BBB zero counter',
                               entry_state_step='1000', stop_state_step='1755',
                               initial_state='AF', initial_history=f'{HISTORY:06X}',
                               receive_byte_source='modelled USART-01 status=02 and data byte at MOVX reads; physical DSP-to-USART wire untraced',
                               scrambler_delays=[5, 18]),
                  cases=rows,
                  interpretation='For both V.26 ter scrambler polynomials, seven decoded zero octets leave AF; eight advance AF to B0. A nonzero decoded byte resets the count, and eight fresh zero octets are required.',
                  limitations=['Each byte enters through the actual state-AF receive dispatcher and its 1DB8/05A3/1BBB calls, with one modeled status and data read; the final handoff to the state-step entry is synthetic rather than a naturally timed main loop.',
                               'The input bytes come from a verified reference scrambler, not from an executed DSC receiver or physical USART RxD wire.',
                               'The counter recognizes eight full zero octets; this test does not establish detection of every unaligned 64-bit zero window.',
                               'State B0 is an observed transition; its exact echo-canceller command and the DSC receive path remain unverified.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print([(row['delay'], row['sequence'], row['final_state'])
           for row in report['cases']])
