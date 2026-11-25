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


@dataclass
class SplitAm2901:
    """Two four-bit slices with explicit high-slice instruction-bit links.

    This is a diagnostic topology, not recovered Nokia wiring. Carry and shift
    pins are cascaded in the ordinary eight-bit order.
    """
    ram: list = field(default_factory=lambda: [0] * 16)
    q: int = 0
    high_from_low: dict = field(default_factory=dict)
    undriven_shift: int = 0
    undriven_shift_reads: int = 0

    def high_instruction(self, low_instruction, proposed_high=None):
        high = low_instruction if proposed_high is None else proposed_high
        for high_bit, low_bit in self.high_from_low.items():
            high = (high & ~(1 << high_bit)) | (((low_instruction >> low_bit) & 1) << high_bit)
        return high

    def step(self, instruction, a, b, d=0, carry=0, ram_in=0, q_in=0,
             high_instruction=None, high_a=None, high_b=None):
        high_instruction = self.high_instruction(instruction, high_instruction)
        high_a = a if high_a is None else high_a
        high_b = b if high_b is None else high_b
        low = Am2901(width=4, ram=[v & 15 for v in self.ram], q=self.q & 15,
                     logic_flags=True)
        high = Am2901(width=4, ram=[v >> 4 for v in self.ram], q=self.q >> 4,
                      logic_flags=True)
        # Destination 1 leaves RAM/Q unchanged, allowing shift inputs and
        # the high-slice carry to be computed from the old simultaneous state.
        lo_f = low.step((instruction & 63) | 64, a, b, d & 15, carry)
        hi_f = high.step((high_instruction & 63) | 64, high_a, high_b, d >> 4,
                         lo_f['carry'])
        lo_dest, hi_dest = instruction >> 6, high_instruction >> 6
        lo_ram_in = hi_f['f'] & 1 if hi_dest in (4, 5) else self.undriven_shift
        hi_ram_in = ram_in & 1
        lo_q_in = high.q & 1 if hi_dest in (4, 5) else self.undriven_shift
        hi_q_in = q_in & 1
        if lo_dest in (6, 7):
            lo_ram_in = ram_in & 1
            lo_q_in = q_in & 1
        if hi_dest in (6, 7):
            hi_ram_in = (lo_f['f'] >> 3) & 1 if lo_dest in (6, 7) else self.undriven_shift
            hi_q_in = (low.q >> 3) & 1 if lo_dest in (6, 7) else self.undriven_shift
        if lo_dest in (4, 5) and hi_dest not in (4, 5):
            self.undriven_shift_reads += 1 + (lo_dest == 4)
        if hi_dest in (6, 7) and lo_dest not in (6, 7):
            self.undriven_shift_reads += 1 + (hi_dest == 6)
        lo_result = low.step(instruction, a, b, d & 15, carry, lo_ram_in, lo_q_in)
        hi_result = high.step(high_instruction, high_a, high_b, d >> 4,
                              lo_result['carry'], hi_ram_in, hi_q_in)
        self.ram = [lower | (upper << 4) for lower, upper in zip(low.ram, high.ram)]
        self.q = low.q | (high.q << 4)
        return dict(f=lo_result['f'] | (hi_result['f'] << 4),
                    y=lo_result['y'] | (hi_result['y'] << 4),
                    carry=hi_result['carry'], overflow=hi_result['overflow'],
                    zero=lo_result['zero'] & hi_result['zero'], sign=hi_result['sign'])


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
