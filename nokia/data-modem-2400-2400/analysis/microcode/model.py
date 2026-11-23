"""Functional Am2901 datapath and Signetics 8X02; no Nokia wiring implied.

Datasheet references and timing limitations are in README.md.
"""
from dataclasses import dataclass, field


@dataclass
class Am2901:
    # width=8 models two slices with ordinary carry and shift cascading.
    width: int = 8
    ram: list = field(default_factory=lambda: [0] * 16)
    q: int = 0
    # Opt in explicitly: historical experiments leave these pins unknown.
    logic_flags: bool = False

    def step(self, instruction, a, b, d=0, carry=0, ram_in=0, q_in=0):
        mask = (1 << self.width) - 1
        av, bv, oldq = self.ram[a], self.ram[b], self.q
        r, s = [(av, oldq), (av, bv), (0, oldq), (0, bv),
                (0, av), (d, av), (d, oldq), (d, 0)][instruction & 7]
        fn = (instruction >> 3) & 7
        lhs, rhs = r, s
        if fn == 1:
            lhs = r ^ mask
        elif fn == 2:
            rhs = s ^ mask
        if fn < 3:
            total = lhs + rhs + carry
            f = total & mask
            cout = (total >> self.width) & 1
            overflow = int(bool((~(lhs ^ rhs) & (lhs ^ f)) & (1 << (self.width - 1))))
        else:
            f = [r | s, r & s, (r ^ mask) & s, r ^ s, (r ^ s) ^ mask][fn - 3]
            # Preserve unknown pins unless the caller selects the defined model.
            cout = overflow = None
            if self.logic_flags:
                # AMD 01566B, p.5-8, Fig.9. '+' in that table means OR.
                if fn in (3, 6):
                    propagate = ((r ^ mask) if fn == 6 else r) | s
                    cout = int(propagate != mask or bool(carry))
                    overflow = cout
                elif fn in (4, 5):
                    generate = ((r ^ mask) if fn == 5 else r) & s
                    cout = int(bool(generate) or bool(carry))
                    overflow = cout
                else:
                    # XNOR's complemented lookahead equation is equivalent
                    # to c[i+1] = !P[i] OR (!G[i] AND c[i]).
                    cout = carry
                    for bit in range(self.width):
                        before = cout
                        p = ((r | s) >> bit) & 1
                        g = ((r & s) >> bit) & 1
                        cout = (1-p) | ((1-g) & cout)
                    overflow = before ^ cout
        dest = (instruction >> 6) & 7
        if dest == 0:
            self.q = f
        elif dest in (2, 3):
            self.ram[b] = f
        elif dest in (4, 5):
            self.ram[b] = (f >> 1) | ((ram_in & 1) << (self.width - 1))
            if dest == 4:
                self.q = (oldq >> 1) | ((q_in & 1) << (self.width - 1))
        elif dest in (6, 7):
            self.ram[b] = ((f << 1) | (ram_in & 1)) & mask
            if dest == 6:
                self.q = ((oldq << 1) | (q_in & 1)) & mask
        return dict(f=f, y=av if dest == 2 else f, carry=cout,
                    overflow=overflow, zero=int(f == 0), sign=f >> (self.width - 1))


class UnknownStack(RuntimeError):
    pass


@dataclass
class X8X02:
    pc: int = 0
    sp: int = 0  # arbitrary index origin; contents are unknown at power-on
    stack: list = field(default_factory=lambda: [None] * 4)
    pushes: int = 0
    pops: int = 0

    def step(self, command, branch=0, test=False):
        nxt = (self.pc + 1) & 1023
        if command == 0:
            nxt = (self.pc + 1 + bool(test)) & 1023
        elif command in (2, 3):
            if command == 3 or test:
                value = self.stack[self.sp]
                if value is None:
                    raise UnknownStack(f'unknown stack at PC {self.pc:03x}')
                nxt = value
            # BLT pops even when TEST is false (Signetics p. 12).
            self.sp = (self.sp - 1) & 3
            self.pops += 1
        elif command in (4, 5):
            if command == 5 or test:
                self.sp = (self.sp + 1) & 3
                self.stack[self.sp] = self.pc if command == 5 else nxt
                self.pushes += 1
                if command == 4:
                    nxt = branch
        elif command == 6:
            if test:
                nxt = branch
        elif command == 7:
            nxt = 0  # RST leaves the stack and pointer unchanged.
        elif command != 1:
            raise ValueError(command)
        self.pc = nxt & 1023
        return self.pc
