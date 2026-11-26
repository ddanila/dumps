"""Model held external SYNDET with RxC gated until a candidate data boundary."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_dual_zero_handoff import controller
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, ROM

SOURCE = HERE / 'receiver_timed_controller_probe.c'
NONZERO = HERE / 'results/receiver-mask04-nonzero-frame-handoff.json'
ZERO = HERE / 'results/receiver-mask04-frame-mode-zero-handoff.json'
OLD = 'if(index==pulse_bit) {synced=1;count=shift=0;}'
NEW = ('if(index<pulse_bit) return; '
       'if(!synced) {synced=1;count=shift=0;}')
GATES = (0, 63, 64, 65, 128)


def source():
    original = SOURCE.read_text()
    if original.count(OLD) != 1:
        raise ValueError('paced 8251 source changed')
    return original.replace(OLD, NEW)


def run(out=HERE / 'results/receiver-rxc-gate-screen.json'):
    nonzero = json.loads(NONZERO.read_text())
    zero = json.loads(ZERO.read_text())
    cases = []
    changed_source = source()
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / 'rxc-gated.c'
        path.write_text(changed_source)
        exe = Path(temporary) / 'rxc-gated'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE), str(path),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        source_rows = [(row['delay'], row['degrees'], row['payload'],
                        row['recovered_line_bytes'], row['trace_digest'],
                        row['aligned'])
                       for row in nonzero['cases']]
        source_rows += [(row['polynomial_delay'], row['degrees'], [0] * 8,
                         row['recovered_line_bytes'], row['trace_digest'],
                         row['controller']['aligned'])
                        for row in zero['cases']]
        for delay, degrees, payload, line_hex, digest, prior_aligned in source_rows:
            values = [int(item, 16) for item in line_hex]
            selector = 0x40 if delay == 5 else 0x60
            gates = {str(gate): controller(exe, delay, selector, gate, values)
                     for gate in GATES}
            aligned = gates['64']
            if (aligned != prior_aligned or
                    aligned['consumed_bytes'] != values or
                    aligned['decoded_bytes'] != payload or
                    aligned['errors'] or aligned['overruns'] or
                    gates['128']['consumed_bytes'] or
                    any(gates[str(gate)]['consumed_bytes'] == values
                        for gate in (0, 63, 65))):
                raise ValueError(('RxC gate control changed', delay, payload[0]))
            cases.append(dict(delay=delay, degrees=degrees, payload=payload,
                              recovered_line_bytes=line_hex,
                              prom_trace_digest=digest, gates=gates))
            print(delay, degrees, payload[0],
                  [(gate, gates[str(gate)]['state'],
                    gates[str(gate)]['consumed_bytes'][:1])
                   for gate in GATES], flush=True)
    paths = [Path(__file__), SOURCE, NONZERO, ZERO, ROM,
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_timed_controller_handoff.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c',
                                       'emu8051.h'))]
    report = dict(experiment='held external SYNDET with gated receive clock',
                  fixture=dict(gate_open_bit=GATES, bit_ticks=BIT_TICKS,
                               syndet='held high before first enabled RxC edge',
                               preamble='64 one bits then eight saved PROM-derived line bytes'),
                  cases=cases,
                  limitations=['The held SYNDET level, RxC gate and its opening event are hypothetical board wiring.',
                               'The narrow 8251 model uses a one-time sync latch; the 8031 ROM executes with synthetic serial completion.',
                               'The DSC PROM traces are verified saved inputs, not rerun by this screen.'],
                  instrumented_source_sha256=hashlib.sha256(changed_source.encode()).hexdigest(),
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
