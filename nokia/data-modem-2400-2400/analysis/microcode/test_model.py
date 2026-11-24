import unittest
import random
from model import Am2901, SplitAm2901, X8X02, UnknownStack


def op(source, function, destination):
    return source | (function << 3) | (destination << 6)


class DatapathTests(unittest.TestCase):
    def test_all_byte_additions_and_borrow(self):
        cpu = Am2901()
        for a in range(256):
            cpu.ram[0] = a
            for b in range(256):
                cpu.ram[1] = b
                for carry in (0, 1):
                    r = cpu.step(op(1, 0, 1), 0, 1, carry=carry)
                    self.assertEqual((r['f'], r['carry']), ((a+b+carry) % 256, int(a+b+carry >= 256)))
                    signed = lambda n: n if n < 128 else n - 256
                    self.assertEqual(r['overflow'], int(not -128 <= signed(a)+signed(b)+carry <= 127))
                    r = cpu.step(op(1, 1, 1), 0, 1, carry=carry)
                    total = b-a-(1-carry)
                    self.assertEqual((r['f'], r['carry']), (total % 256, int(total >= 0)))
                    r = cpu.step(op(1, 2, 1), 0, 1, carry=carry)
                    total = a-b-(1-carry)
                    self.assertEqual((r['f'], r['carry']), (total % 256, int(total >= 0)))

    def test_source_selection(self):
        cpu = Am2901(ram=[0x12, 0x40] + [0]*14, q=0x03)
        for source, expected in enumerate([0x15, 0x52, 3, 0x40, 0x12, 0x92, 0x83, 0x80]):
            self.assertEqual(cpu.step(op(source, 0, 1), 0, 1, d=0x80)['f'], expected)

    def test_logic(self):
        cpu = Am2901(ram=[0xC3, 0x5A] + [0]*14)
        for fn, expected in enumerate([0xDB, 0x42, 0x18, 0x99, 0x66], 3):
            result = cpu.step(op(1, fn, 1), 0, 1)
            self.assertEqual(result['f'], expected)
            self.assertIsNone(result['carry'])

    def test_destinations_and_external_shift_inputs(self):
        for dest in range(8):
            cpu = Am2901(ram=[0x12, 0x40]+[0]*14, q=0x81)
            r = cpu.step(op(7, 3, dest), 0, 1, d=0xA5, ram_in=1, q_in=0)
            self.assertEqual(r['y'], 0x12 if dest == 2 else 0xA5)
            self.assertEqual(cpu.ram[1], [0x40, 0x40, 0xA5, 0xA5, 0xD2, 0xD2, 0x4B, 0x4B][dest])
            self.assertEqual(cpu.q, [0xA5, 0x81, 0x81, 0x81, 0x40, 0x81, 0x02, 0x81][dest])

    def test_datasheet_logic_flags_four_bit_equations(self):
        cpu=Am2901(width=4,logic_flags=True)
        for r in range(16):
            for s in range(16):
                cpu.ram[0],cpu.ram[1]=r,s
                for carry in (0,1):
                    for fn in range(3,8):
                        rr=r^15 if fn in (5,6) else r
                        p=[((rr|s)>>i)&1 for i in range(4)]
                        g=[((rr&s)>>i)&1 for i in range(4)]
                        if fn in (3,6):
                            expected=(1-(p[3]&p[2]&p[1]&p[0]))|carry
                            overflow=expected
                        elif fn in (4,5):
                            expected=g[3]|g[2]|g[1]|g[0]|carry
                            overflow=expected
                        else:
                            # Expanded Cn+4 and OVR expressions from Figure 9,
                            # separately from the model's bitwise recurrence.
                            expected=1-(g[3]|(p[3]&g[2])|(p[3]&p[2]&g[1])|
                                        (p[3]&p[2]&p[1]&p[0]&(g[0]|(1-carry))))
                            ng=[1-x for x in g];np=[1-x for x in p]
                            c3=np[2]|(ng[2]&np[1])|(ng[2]&ng[1]&np[0])|(ng[2]&ng[1]&ng[0]&carry)
                            c4=np[3]|(ng[3]&np[2])|(ng[3]&ng[2]&np[1])|(ng[3]&ng[2]&ng[1]&np[0])|(ng[3]&ng[2]&ng[1]&ng[0]&carry)
                            overflow=c3^c4
                        got=cpu.step(op(1,fn,1),0,1,carry=carry)
                        self.assertEqual((got['carry'],got['overflow']),(expected,overflow),(r,s,carry,fn))

    def test_logic_flags_ripple_across_two_slices(self):
        for r in (0,1,15,16,127,128,240,254,255):
            for s in (0,1,15,16,127,128,240,254,255):
                for carry in (0,1):
                    for fn in range(3,8):
                        lo=Am2901(width=4,logic_flags=True,ram=[r&15,s&15]+[0]*14)
                        hi=Am2901(width=4,logic_flags=True,ram=[r>>4,s>>4]+[0]*14)
                        wide=Am2901(logic_flags=True,ram=[r,s]+[0]*14)
                        l=lo.step(op(1,fn,1),0,1,carry=carry)
                        h=hi.step(op(1,fn,1),0,1,carry=l['carry'])
                        w=wide.step(op(1,fn,1),0,1,carry=carry)
                        self.assertEqual((w['f'],w['carry'],w['overflow']),((h['f']<<4)|l['f'],h['carry'],h['overflow']))

    def test_two_slice_carry(self):
        lo, hi, wide = Am2901(width=4), Am2901(width=4), Am2901()
        lo.ram[0], lo.ram[1] = 15, 1
        hi.ram[0], hi.ram[1] = 7, 0
        wide.ram[0], wide.ram[1] = 127, 1
        l = lo.step(op(1, 0, 3), 0, 1)
        h = hi.step(op(1, 0, 3), 0, 1, carry=l['carry'])
        w = wide.step(op(1, 0, 3), 0, 1)
        self.assertEqual(w['f'], (h['f'] << 4) | l['f'])
        self.assertEqual(w['overflow'], 1)

    def test_split_slices_match_wide_model_without_cross_links(self):
        rng=random.Random(2901)
        for instruction in range(512):
            ram=[rng.randrange(256) for _ in range(16)]
            q,d=rng.randrange(256),rng.randrange(256)
            a,b=rng.randrange(16),rng.randrange(16)
            carry,ram_in,q_in=(rng.randrange(2) for _ in range(3))
            wide=Am2901(ram=ram[:],q=q,logic_flags=True)
            split=SplitAm2901(ram=ram[:],q=q)
            expected=wide.step(instruction,a,b,d,carry,ram_in,q_in)
            actual=split.step(instruction,a,b,d,carry,ram_in,q_in)
            self.assertEqual((actual,split.ram,split.q),
                             (expected,wide.ram,wide.q),instruction)

    def test_split_instruction_link_changes_only_high_slice_destination(self):
        instruction=op(7,3,0)  # D|0, load Q; source bit I2 is high.
        split=SplitAm2901(q=0xC0,high_from_low={6:2})
        result=split.step(instruction,0,0,d=0xA5)
        self.assertEqual(split.high_instruction(instruction),instruction | (1<<6))
        self.assertEqual(split.q,0xC5)
        self.assertEqual(result['y'],0xA5)

    def test_split_accepts_independent_high_instruction_before_links(self):
        low_instruction=op(7,3,0)  # D|0, load Q.
        high_instruction=op(2,3,0)  # 0|Q, load Q.
        split=SplitAm2901(q=0xC0)
        result=split.step(low_instruction,0,0,d=0xA5,
                          high_instruction=high_instruction)
        self.assertEqual(result['y'],0xC5)
        self.assertEqual(split.q,0xC5)
        linked=SplitAm2901(high_from_low={4:1})
        self.assertEqual(linked.high_instruction(low_instruction,high_instruction),
                         high_instruction | (1<<4))

    def test_split_asymmetric_shift_uses_explicit_undriven_level(self):
        instruction=op(0,3,4)  # Low Q shifts right; high I8 is cleared.
        zero=SplitAm2901(q=0x81,high_from_low={8:0},undriven_shift=0)
        one=SplitAm2901(q=0x81,high_from_low={8:0},undriven_shift=1)
        zero.step(instruction,0,0)
        one.step(instruction,0,0)
        self.assertEqual(zero.q & 15,0)
        self.assertEqual(one.q & 15,8)
        self.assertEqual((zero.undriven_shift_reads,one.undriven_shift_reads),(2,2))


class SequencerTests(unittest.TestCase):
    def test_increment_skip_wrap(self):
        cpu = X8X02(pc=1023)
        self.assertEqual(cpu.step(1), 0)
        self.assertEqual(cpu.step(0, test=True), 2)
        self.assertEqual(cpu.step(0, test=False), 3)

    def test_call_return(self):
        cpu = X8X02(pc=12)
        self.assertEqual(cpu.step(4, branch=100, test=False), 13)
        self.assertEqual(cpu.pushes, 0)
        self.assertEqual(cpu.step(4, branch=100, test=True), 100)
        self.assertEqual(cpu.step(3), 14)

    def test_loop_false_still_pops(self):
        cpu = X8X02(pc=20)
        self.assertEqual(cpu.step(5), 21)
        self.assertEqual(cpu.step(2, test=False), 22)
        self.assertEqual(cpu.sp, 0)
        self.assertEqual(cpu.pops, 1)
        cpu.step(5)
        self.assertEqual(cpu.step(2, test=True), 22)

    def test_branch_reset_preserves_stack(self):
        cpu = X8X02(pc=5)
        cpu.step(5)
        self.assertEqual(cpu.step(6, branch=88, test=False), 7)
        self.assertEqual(cpu.step(6, branch=88, test=True), 88)
        self.assertEqual(cpu.step(7), 0)
        self.assertEqual(cpu.step(3), 5)

    def test_uninitialized_stack_is_not_zero(self):
        with self.assertRaises(UnknownStack):
            X8X02().step(3)

    def test_four_nested_calls(self):
        cpu = X8X02()
        for address in [100, 200, 300, 400]:
            cpu.step(4, branch=address, test=True)
        for expected in [301, 201, 101, 1]:
            self.assertEqual(cpu.step(3), expected)


if __name__ == '__main__':
    unittest.main()
