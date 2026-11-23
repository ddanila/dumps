"""Small four-state, fixed-width logic values. Bit 0 is least significant."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    bits: tuple

    @classmethod
    def x(cls, width):
        return cls(('X',) * width)

    @classmethod
    def z(cls, width):
        return cls(('Z',) * width)

    @classmethod
    def of(cls, number, width):
        if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number < 1 << width:
            raise ValueError(f'{number!r} is not an unsigned {width}-bit value')
        return cls(tuple((number >> i) & 1 for i in range(width)))

    def integer(self):
        if any(b not in (0, 1) for b in self.bits):
            return None
        return sum(b << i for i, b in enumerate(self.bits))

    def text(self):
        return ''.join(str(b) for b in reversed(self.bits))

    def __invert__(self):
        return Word(tuple(1-b if b in (0, 1) else 'X' for b in self.bits))

    def binary(self, other, kind):
        if len(self.bits) != len(other.bits):
            raise ValueError('width mismatch')
        def bit(a, b):
            if kind == 'and' and (a == 0 or b == 0): return 0
            if kind == 'or' and (a == 1 or b == 1): return 1
            if a not in (0, 1) or b not in (0, 1): return 'X'
            return {'and': a & b, 'or': a | b, 'xor': a ^ b}[kind]
        return Word(tuple(bit(a, b) for a, b in zip(self.bits, other.bits)))

    def __and__(self, other): return self.binary(other, 'and')
    def __or__(self, other): return self.binary(other, 'or')
    def __xor__(self, other): return self.binary(other, 'xor')

    def merge(self, other):
        return Word(tuple(a if a == b else 'X' for a, b in zip(self.bits, other.bits)))

    def gate(self, enable_n):
        en = enable_n.integer()
        return self if en == 0 else Word.z(len(self.bits)) if en == 1 else Word.x(len(self.bits))

    def add(self, other, carry):
        out, cin_sign = [], carry
        for i, (a, b) in enumerate(zip(self.bits, other.bits)):
            a, b = Word((a,)), Word((b,))
            if i == len(self.bits)-1: cin_sign = carry
            out.extend((a ^ b ^ carry).bits)
            carry = (a & b) | ((a | b) & carry)
        return Word(tuple(out)), carry, cin_sign ^ carry


def mux(a, b, select):
    s = select.integer()
    return a if s == 0 else b if s == 1 else a.merge(b)


def resolve(drivers):
    if not drivers: raise ValueError('empty bus')
    out = []
    for bits in zip(*(d.bits for d in drivers)):
        active = [b for b in bits if b != 'Z']
        if not active: out.append('Z')
        elif 0 in active and 1 in active: raise ValueError('bus contention: active 0 and 1 drivers')
        elif 'X' in active: out.append('X')
        else: out.append(active[0])
    return Word(tuple(out))
