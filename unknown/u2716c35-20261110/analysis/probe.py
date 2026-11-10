#!/usr/bin/env python3
"""Execute isolated original-ROM routines with libz80ex; no hardware access.

The matrix port model is an inferred interface, not an emulation of an identified
board. RAM/stack are synthetic. No missing firmware routines are stubbed.
"""
import ctypes as C
import hashlib
import json
from pathlib import Path

ROM = (Path(__file__).resolve().parent.parent / 'rom.bin').read_bytes()
assert hashlib.sha256(ROM).hexdigest() == 'b97cfb4b68b56690c27730daaa347a8780579c8aa75d0169979cc63e33044b34'
lib = C.CDLL('libz80ex.so.1')
P, W, B = C.c_void_p, C.c_uint16, C.c_uint8
MR = C.CFUNCTYPE(B, P, W, C.c_int, P)
MW = C.CFUNCTYPE(None, P, W, B, P)
PR = C.CFUNCTYPE(B, P, W, P)
PW = C.CFUNCTYPE(None, P, W, B, P)
IR = C.CFUNCTYPE(B, P, P)
lib.z80ex_create.argtypes = [MR, P, MW, P, PR, P, PW, P, IR, P]
lib.z80ex_create.restype = P
lib.z80ex_get_reg.argtypes = [P, C.c_int]
lib.z80ex_get_reg.restype = W
lib.z80ex_set_reg.argtypes = [P, C.c_int, W]
lib.z80ex_step.argtypes = [P]
lib.z80ex_destroy.argtypes = [P]


class Machine:
    def __init__(self, keys=()):
        self.mem = bytearray(65536)
        self.mem[0x6800:0x7000] = ROM
        self.keys = set(keys)
        self.selector = 0xA0
        self.reads = []
        self.writes = []
        self.errors = []
        self.callbacks = [MR(lambda cpu, a, m1, u: self.mem[a]),
                          MW(self.write), PR(self.port_read), PW(self.port_write),
                          IR(lambda cpu, u: 0xFF)]
        args = [x for cb in self.callbacks for x in (cb, None)]
        self.cpu = lib.z80ex_create(*args)

    def write(self, cpu, address, value, user):
        if 0x6800 <= address < 0x7000:
            self.errors.append('ROM write')
        self.mem[address] = value

    def port_read(self, cpu, port, user):
        port &= 255
        if port == 0xC8:
            return self.selector
        if port == 0xC9:
            row = self.selector & 15
            self.reads.append(row)
            return 255 ^ sum(1 << bit for r, bit in self.keys if r == row)
        self.errors.append(f'unexpected input {port:02x}')
        return 255

    def port_write(self, cpu, port, value, user):
        self.writes.append([port & 255, value])
        if port & 255 == 0xC8:
            self.selector = value
        else:
            self.errors.append(f'unexpected output {port & 255:02x}')

    def word(self, address, value):
        self.mem[address:address+2] = value.to_bytes(2, 'little')

    def call(self, address, af=0, de=0):
        for reg, value in [(0, af), (2, de), (10, address), (11, 0xF000)]:
            lib.z80ex_set_reg(self.cpu, reg, value)
        self.word(0xF000, 0xFFFF)
        for steps in range(20000):
            pc = lib.z80ex_get_reg(self.cpu, 10)
            if pc == 0xFFFF:
                assert not self.errors, self.errors
                return steps
            assert 0x69DE <= pc < 0x6DF9, f'escaped available code: {pc:04x}'
            lib.z80ex_step(self.cpu)
        raise AssertionError('step limit')

    def close(self):
        lib.z80ex_destroy(self.cpu)


def main():
    cases = []
    for row in range(12):
        for bit in range(8):
            m = Machine([(row, bit)])
            m.call(0x6AE4)
            assert m.reads == list(range(12))
            assert m.selector == 0xAF  # preserves upper nibble, deselects matrix
            assert m.mem[0x789F] == 2 * (row * 8 + bit)
            assert m.mem[0x78A2] == 1 and m.mem[0x78A5] == 1
            # Previous snapshot contains the same pressed key, state 1.
            m.mem[0x78A7:0x78AE] = m.mem[0x789F:0x78A6]
            m.call(0x6AE4)
            assert m.mem[0x78A2] == 2
            m.keys.clear()
            m.call(0x6AE4)
            assert m.mem[0x78A5] == 0
            m.close()
    cases.append('96 matrix positions: fresh=1, held=2, released count=0')
    for count in (0, 2, 3, 4):
        m = Machine([(0, b) for b in range(count)])
        m.call(0x6AE4)
        assert m.mem[0x78A5] == count
        if count == 4:
            assert m.reads == [0]  # abort before storing fourth key
        m.close()
    cases.append('0/2/3/4 simultaneous keys; fourth-key overflow sentinel')
    for pointer, next_pointer in [(0x7942, 0x7943), (0x7981, 0x7942)]:
        m = Machine()
        m.word(0x78B3, pointer)
        m.word(0x78B5, 0x7960)
        m.call(0x6CE7, af=0x5A00)
        assert m.mem[pointer] == 0x5A
        assert int.from_bytes(m.mem[0x78B3:0x78B5], 'little') == next_pointer
        m.word(0x78B5, pointer)
        m.call(0x6D0B)
        assert m.mem[0x78B2] == 0x5A and m.mem[0x78B1] & 1
        assert int.from_bytes(m.mem[0x78B5:0x78B7], 'little') == next_pointer
        m.close()
    cases.append('64-byte queue enqueue/dequeue and wrap at 7982h to 7942h')
    print(json.dumps({'sha256': hashlib.sha256(ROM).hexdigest(),
                      'load_address': '6800h', 'passed': cases,
                      'limitations': 'Isolated routines, synthetic RAM and inferred matrix ports; no full-system boot or physical hardware.'}, indent=2))


if __name__ == '__main__':
    main()
