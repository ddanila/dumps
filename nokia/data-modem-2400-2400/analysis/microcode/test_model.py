import unittest
from model import Am2901, X8X02, UnknownStack


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
