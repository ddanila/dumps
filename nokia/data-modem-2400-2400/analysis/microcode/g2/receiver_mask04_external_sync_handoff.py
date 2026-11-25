"""Clock the recovered PROM bitstream into an external-sync 8251A candidate."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from receiver_mask04_controller_zero_handoff import (CORE, DATA_BYTES, HERE,
                                                     HISTORY, ROM, controller_probe)
from common import save

SOURCE = HERE / 'results/receiver-mask04-controller-zero-handoff.json'
MODE = 0xCC
SYNC_CHAR = 0xFF
COMMAND = 0x15
PREAMBLE_BITS = 64
BIT_CYCLES = 6000
PULSE_OFFSETS = (-8, -1, 0, 1)


class ExternalSyncReceiver:
    """Only external SYNDET, RxC rising-edge shift and immediate CPU reads."""

    def __init__(self, mode, sync_char, command):
        if (mode != MODE or sync_char != SYNC_CHAR or command != COMMAND or
                not (mode & 0x40) or (mode & 3) or
                (mode & 0x0C) != 0x0C or not (command & 4)):
            raise ValueError('unexpected 8251A receive programming')
        self.synced = False
        self.count = 0
        self.shift = 0
        self.rx_ready = False
        self.data = None
        self.completed = []
        self.sync_edges = []

    def rising_rxc(self, index, rxd, external_syndet):
        if external_syndet and not self.synced:
            self.synced = True
            self.sync_edges.append(index)
            self.count = self.shift = 0
        if not self.synced:
            return
        self.shift |= rxd << self.count
        self.count += 1
        if self.count == 8:
            self.data = self.shift
            self.rx_ready = True
            self.completed.append(dict(last_rxc_index=index, byte=self.data))
            self.count = self.shift = 0

    def read_status(self):
        return 2 if self.rx_ready else 0

    def read_data(self):
        if not self.rx_ready:
            raise ValueError('CPU read before RxRDY')
        value = self.data
        self.rx_ready = False
        self.data = None
        return value


def serial_bits(case):
    preamble = case['recovered_preamble_dibits']
    if len(preamble) != 31 or any(dibit != 3 for dibit in preamble):
        raise ValueError('real-PROM reversal preamble changed')
    values = [int(value, 16) for value in case['recovered_line_bytes']]
    if len(values) != DATA_BYTES:
        raise ValueError('real-PROM data byte count changed')
    # First differential dibit is unobserved; the supplied reversal fixture
    # says it is 11. The following 62 ones are PROM-derived decisions.
    bits = [1, 1] + [bit for dibit in preamble
                     for bit in (dibit & 1, (dibit >> 1) & 1)]
    bits += [(value >> bit) & 1 for value in values for bit in range(8)]
    if len(bits) != 128 or bits[:PREAMBLE_BITS] != [1] * PREAMBLE_BITS:
        raise ValueError('reconstructed serial stream changed')
    return bits, values


def clock_candidate(bits, pulse_index):
    receiver = ExternalSyncReceiver(MODE, SYNC_CHAR, COMMAND)
    cpu_bytes = []
    statuses = []
    for index, bit in enumerate(bits):
        receiver.rising_rxc(index, bit, index == pulse_index)
        status = receiver.read_status()
        if status & 2:
            statuses.append(dict(rxc_index=index, status=status))
            cpu_bytes.append(receiver.read_data())
    return dict(pulse_index=pulse_index,
                syndet_rising_edges=receiver.sync_edges,
                bytes=[f'{value:02X}' for value in cpu_bytes],
                rxrdy_events=statuses,
                first_incomplete_character_bits=receiver.count,
                completed=receiver.completed), cpu_bytes


def run(out=HERE / 'results/receiver-mask04-external-sync-handoff.json'):
    source = json.loads(SOURCE.read_text())
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'zero-run-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-function',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'zero_run_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for prior in source['cases']:
            bits, expected = serial_bits(prior)
            offsets = []
            for offset in PULSE_OFFSETS:
                shifted, received = clock_candidate(bits, PREAMBLE_BITS + offset)
                controller = controller_probe(exe, prior['polynomial_delay'], received)
                shifted.update(offset_from_first_data_bit=offset,
                               matches_prom_bytes=received == expected,
                               controller_state=f'{controller["state_after"]:02X}',
                               controller_zero_octets=controller['zero_octets'],
                               controller_decoded_bytes=[f'{row["decoded"]:02X}'
                                                         for row in controller['octets']],
                               outgoing_frame=' '.join(f'{value:02X}'
                                                       for value in controller['wire']))
                offsets.append(shifted)
            no_pulse, empty = clock_candidate(bits, -1)
            if (empty or no_pulse['rxrdy_events'] or
                    offsets[2]['bytes'] != prior['recovered_line_bytes'] or
                    offsets[2]['controller_state'] != 'B0' or
                    offsets[0]['controller_state'] != 'AF' or
                    offsets[1]['controller_state'] != 'AF' or
                    offsets[3]['controller_state'] != 'AF' or
                    [len(row['bytes']) for row in offsets] != [9, 8, 8, 7]):
                raise ValueError(('external sync handoff changed',
                                  prior['polynomial_delay'], prior['degrees']))
            cases.append(dict(polynomial_delay=prior['polynomial_delay'],
                              degrees=prior['degrees'],
                              real_prom_trace_digest=prior['real_prom_trace_digest'],
                              reconstructed_bit_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                              assumed_first_preamble_dibit=3,
                              recovered_preamble_dibits=31,
                              pulse_offsets=offsets,
                              no_syndet_rxrdy_events=0))
    paths = [Path(__file__), SOURCE,
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'zero_run_probe.c', ROM,
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c'))]
    report = dict(experiment='external-SYNDET bit-clock handoff from saved real-PROM receive traces to executed 8031 AF detector',
                  fixture=dict(controller_programming='CC FF 15: eight-bit synchronous, external SYNDET input, Rx enabled',
                               rxd_pin=3, rxc_pin=25, syndet_pin=16,
                               assumed_bit_cycles=BIT_CYCLES,
                               assumed_syndet='one-bit high pulse asserted before selected RxC rising edge',
                               receiver_model='RxD sampled on RxC rising edge; external SYNDET starts eight-bit LSB-first assembly on next rising edge; CPU reads each completed byte immediately',
                               tested_pulse_offsets=PULSE_OFFSETS,
                               intel_datasheet='https://deramp.com/downloads/intel/8251A.pdf'),
                  cases=cases,
                  limitations=['The external SYNDET pulse, RxD/RxC wires and 6000-cycle bit clock are assumptions; no photographed source for SYNDET has been identified.',
                               'The first reversal dibit is supplied by the reference fixture because differential PROM readout cannot observe it.',
                               'The shift/RxRDY model covers only this synchronous external-sync path and assumes immediate CPU reads; it is not a full 8251A emulation.',
                               'The preserved 8031 AF dispatcher is entered explicitly and receives the modeled bytes through its prior status/data read probe.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for case in result['cases']:
        print(case['polynomial_delay'], case['degrees'],
              [(x['offset_from_first_data_bit'], x['controller_state'])
               for x in case['pulse_offsets']])
