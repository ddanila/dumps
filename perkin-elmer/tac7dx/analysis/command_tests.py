#!/usr/bin/env python3
"""Execute original parser/dispatcher from the synthetic boot snapshot.
A test-only reset-vector override selects A831; a RAM sentinel receives RTS.
No request is sent to a physical instrument. Each request has fresh boot RAM.
"""
from pathlib import Path
import concurrent.futures
import csv
import json
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
requests = ['$' + row['character']
            for row in csv.DictReader((BASE / 'commands.csv').open())
            if row['supported'] == 'True']
requests += ['$~', '$I,1', '$2,1', '$2,0', '$2,999', '$J,100', '$J,-100',
             '$%,1', 'garbage', '$I,123456789', '$I,1,2,3']


def run(request):
    with tempfile.TemporaryDirectory(prefix='tac7dx-command-') as temporary:
        out = Path(temporary)
        subprocess.run(['python3', str(BASE / 'run.py'), '--request', request,
                        '--seconds', '1', '--output', str(out)],
                       check=True, stdout=subprocess.DEVNULL)
        memory = (out / 'memory.bin').read_bytes()
        word = lambda address: int.from_bytes(memory[address:address + 2], 'big')
        regs = dict(line.split('\t') for line in
                    (out / 'registers.tsv').read_text().splitlines())
        pc = int(regs['PC'])
        start, end, capacity = word(0xba9), word(0xbab), word(0xbae)
        assert capacity and 0 <= start < capacity and 0 <= end < capacity
        indices = (range(start, end) if end >= start
                   else list(range(start, capacity)) + list(range(end)))
        reply = bytes(memory[0xbb0 + j] for j in indices)
        return {
            'request': request + '\r',
            'reply': reply.decode('ascii', errors='backslashreplace'),
            'returned': pc in (0x2f00, 0x2f01, 0x2f02),
            'pc': f'{pc:04x}',
            'instrument_type': memory[0x197],
            'error_bytes': memory[0xb33:0xb35].hex(),
            'parameter_count': memory[0xba6],
        }


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(run, requests))
(BASE / 'command-results.json').write_text(json.dumps(results, indent=2) + '\n')
for result in results:
    print(repr(result['request']), repr(result['reply']), result['returned'], result['pc'])
