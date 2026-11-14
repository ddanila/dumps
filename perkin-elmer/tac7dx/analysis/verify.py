#!/usr/bin/env python3
"""Check preserved experiment outputs, including faults and a complete IRQ."""
from pathlib import Path
import csv
import json

BASE = Path(__file__).resolve().parent
RESULTS = BASE / 'results'


def memory(case):
    data = (RESULTS / case / 'memory.bin').read_bytes()
    assert len(data) == 65536, case
    return data


def log(case):
    return (RESULTS / case / 'io.tsv').read_text()


def serial(case, port, direction):
    rows = csv.DictReader((RESULTS / case / 'serial.tsv').open(), delimiter='\t')
    return bytes(int(r['byte'], 16) for r in rows
                 if r['port'] == port and r['kind'] == direction)


u35 = (BASE.parent / 'u35-n5208003-27256-read.bin').read_bytes()
u36 = (BASE.parent / 'u36-n5208004-27256-read.bin').read_bytes()
assert len(u35) == len(u36) == 32768
assert u35[:16384] == u35[16384:]
for data in (u35[16384:], u36):
    assert int.from_bytes(data[:2], 'big') == sum(data[2:]) & 65535

boot = memory('boot')
assert boot[0x4000:] == u35[16384:] + u36, 'Boot must execute unchanged ROMs'
for name in ('ROM', 'RAM', 'PIA', 'clock', 'type', 'analog', 'serial'):
    assert f'CHECK {name}-check-return A=00' in log('boot'), name
assert 'CHECK main-loop' in log('boot')
assert 'CHECK diagnostic-failure' not in log('boot')
for port in ('3080', '3100'):
    for direction in ('TX', 'RX'):
        assert serial('boot', port, direction) == b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

assert serial('bad-rom', '3080', 'TX') == b'%,2,01\r'
assert serial('missing-clock', '3080', 'TX') == b'%,6,FF\r'
assert 'CHECK ROM-check-return A=01' in log('bad-rom')
assert 'CHECK clock-check-return A=01' in log('missing-clock')
for case in ('bad-rom', 'missing-clock'):
    assert 'CHECK diagnostic-failure' in log(case)
    assert 'CHECK main-loop' not in log(case)

commands = json.loads((BASE / 'command-results.json').read_text())
assert len(commands) == 64
by_request = {r['request']: r for r in commands}
supported = [r for r in csv.DictReader((BASE / 'commands.csv').open())
             if r['supported'] == 'True']
assert len(supported) == 53
assert all('$' + r['character'] + '\r' in by_request for r in supported)
expected = {'$i': 'i,TAC7,N5208003REVA', '$I': 'I,1,0', '$%': '%,0,0',
            '$J': 'J,1000,0', '$J,100': 'J,100,0', '$J,-100': '!,4,0',
            '$2,1': '2,1,0', '$2,0': '2,0,0', '$2,999': '!,4,0',
            '$~': '!,3,0', '$I,1': '!,2,0', '$S': '!,5,1', '$[': '!,5,4'}
for request, reply in expected.items():
    assert by_request[request + '\r']['reply'] == reply + '\r', request
assert [r['request'] for r in commands if not r['returned']] == ['$#\r']
assert by_request['$#\r']['reply'] == '#,0,0\r'
assert by_request['garbage\r']['reply'] == ''

irq = memory('irq')
for name in ('IRQ-entry', 'periodic-service', 'channel-scan', 'IRQ-return', 'test-return'):
    assert f'CHECK {name}' in log('irq'), name
word = lambda data, a: int.from_bytes(data[a:a + 2], 'big')
assert word(boot, 0x171e) == 200 and word(irq, 0x171e) == 199
assert boot[0xb90] == 0 and irq[0xb90] == 1
assert boot[0x155c] == 0 and irq[0x155c] == 1
assert irq[0x1ac9] == 0
assert irq[0x1720:0x1726] != boot[0x1720:0x1726]
assert irq[0x4000:0xfffe] == boot[0x4000:0xfffe], 'Only test reset vector may differ'
assert (RESULTS / 'boot/highram.bin').read_bytes() != (RESULTS / 'irq/highram.bin').read_bytes()
regs = dict(line.split('\t') for line in (RESULTS / 'irq/registers.tsv').read_text().splitlines())
assert int(regs['PC']) in (0x2f00, 0x2f01, 0x2f02)
assert int(regs['S']) == 0x1c7c
for case in ('boot', 'bad-rom', 'missing-clock', 'irq'):
    assert 'LUA ERROR' not in (RESULTS / case / 'mame.log').read_text()
print('PASS: ROM integrity, startup, two faults, 64 commands, and periodic IRQ')
