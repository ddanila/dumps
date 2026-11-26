"""Clock 16 DSC-recovered A4/A5 bytes through modeled 8251 and real 8031."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from zero_run_detector import HISTORY, ROM
from controller_scrambler import transform
from joint_mask04_12a_phase_timing_map import decode
from joint_mask04_buffered_serial_handoff import CONTROLLER_C
from receiver_mask04_dual_zero_handoff import CORE, controller
from receiver_mask04_serial_candidate import bytes_lsb_first

HERE = Path(__file__).resolve().parent
DSC = HERE / 'results/joint-mask04-12a-controller-continuation.json'
PACED = HERE / 'results/main-loop-usart-txready-17.json'
PULSES = (65, 66, 67)


def compiled_probe(directory):
    source = CONTROLLER_C.read_text()
    changes = (
        ('input[8]', 'input[16]'),
        ('index<64?1:(input[(index-64)/8]>>((index-64)%8))&1',
         'index<66?1:(input[(index-66)/8]>>((index-66)%8))&1'),
        ('argc!=15', 'argc!=23'),
        ('pulse_bit>128', 'pulse_bit>194'),
        ('j<8', 'j<16'),
        ('(128+10)*bit_ticks', '(194+10)*bit_ticks'),
        ('next_bit<128', 'next_bit<194'),
    )
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('controller probe injection point changed', old))
        source = source.replace(old, new)
    c_file = directory / 'receiver-16.c'
    exe = directory / 'receiver-16'
    c_file.write_text(source)
    subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                    '-DSAT_TRACE', '-I', str(CORE), str(c_file),
                    *(str(CORE / name) for name in
                      ('core.c', 'opcodes.c', 'disasm.c')),
                    '-o', str(exe)], check=True)
    return exe, hashlib.sha256(source.encode()).hexdigest()


def independent_descramble(values, delay):
    history = HISTORY
    decoded = []
    for value in values:
        history, byte = transform(history, value, delay, inverse=True)
        decoded.append(byte)
    return decoded


def run(out=HERE / 'results/joint-mask04-12a-16byte-reverse-handoff.json'):
    dsc = json.loads(DSC.read_text())
    paced = json.loads(PACED.read_text())
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        exe, probe_sha = compiled_probe(Path(temp))
        for selector, delay in (('40', 5), ('60', 18)):
            row = next(c for c in dsc['cases'] if c['selector'] == selector)
            if row['training_exact_maps'] != 1 or len(row['candidates']) != 1:
                raise ValueError(('A4-trained phase map changed', selector))
            phase = {int(key, 16): value for key, value in
                     row['candidates'][0]['phase'].items()}
            dibits = decode(row['states'], phase)[33:97]
            if len(dibits) != 64 or any(value is None for value in dibits):
                raise ValueError(('DSC readout incomplete', selector))
            recovered = bytes_lsb_first([
                bit for dibit in dibits
                for bit in (dibit & 1, (dibit >> 1) & 1)])
            offered = [int(value, 16) for value in
                       row['training_line_bytes'] + row['payload_line_bytes']]
            if len(recovered) != 16 or recovered != offered:
                raise ValueError(('DSC readout differs from controller source', selector))
            paced_cases = [c for c in paced['cases'] if c['selector'] == selector]
            if len(paced_cases) != 8 or any(
                    [int(value, 16) for value in c['aligned_dsc_bytes']] != recovered
                    for c in paced_cases):
                raise ValueError(('paced TxD source differs from DSC readout', selector))
            independent = independent_descramble(recovered, delay)
            handoffs = {}
            for pulse in PULSES:
                result = controller(exe, delay, int(selector, 16), pulse, recovered)
                handoffs[str(pulse)] = result
            good = handoffs['66']
            if (good['errors'] or good['overruns'] or good['state'] != 0xAF or
                    good['completed'] != 16 or good['consumed'] != 16 or
                    good['consumed_bytes'] != recovered or
                    good['decoded_bytes'] != independent):
                raise ValueError(('aligned reverse handoff failed', selector, good))
            if any(handoffs[str(pulse)]['consumed_bytes'] == recovered
                   for pulse in (65, 67)):
                raise ValueError(('misaligned sync control passed', selector))
            cases.append(dict(selector=selector, delay=delay,
                              recovered_dsc_bytes=[f'{value:02X}' for value in recovered],
                              independent_decoded_bytes=[f'{value:02X}' for value in independent],
                              paced_txd_cases=len(paced_cases),
                              handoffs=handoffs))
            print(selector, 'aligned',good['consumed'],
                  'errors',good['errors'], 'overruns',good['overruns'], flush=True)
    paths = (Path(__file__), DSC, PACED, CONTROLLER_C, ROM,
             HERE.parents[1] / 'controller_scrambler.py',
             HERE / 'joint_mask04_12a_phase_timing_map.py')
    report = dict(experiment='16-byte DSC receive to modeled 8251 and unchanged 8031',
                  fixture=dict(input='64 dibits decoded from executed DSC states with A4-trained map',
                               pulses=PULSES, aligned_pulse=66,
                               receiver='modeled 8251 external SYNDET, 2400-bit/s RxC, one-byte receive buffer carrying 16 characters',
                               controller='unchanged 8031 ROM in AF, preserved history'),
                  controller_probe_sha256=probe_sha,
                  cases=cases,
                  limitations=['The DSC phase map and RxD/RxC/SYNDET wiring are external photo-compatible hypotheses.',
                               'The 8031 probe begins in AF; it does not naturally traverse its earlier A3/A4 states while receiving these bytes.',
                               'Matched aligned bytes under this model do not establish a physical receive circuit.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
