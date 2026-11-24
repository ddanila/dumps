import unittest
from table_signatures import ROM, inspect, phase_sequence, occurrences


class TableSignatures(unittest.TestCase):
    def test_actual_rom_matches_and_negative_candidates(self):
        report=inspect(ROM.read_bytes())
        self.assertEqual(report['gray16']['exact_occurrences'],['07C'])
        self.assertFalse(report['gray16']['candidate_068_matches'])
        self.assertFalse(report['gray16']['candidate_06c_matches'])
        self.assertTrue(report['sine16']['exact'])
        self.assertTrue(report['sine16']['wrap_exact'])
        self.assertTrue(report['sine256_quarter']['exact'])

    def test_differential_increment_and_reversals(self):
        increments=list(ROM.read_bytes()[0x7c:0x80])
        for initial in range(16):
            phases=phase_sequence([0,1,2,3],increments,initial)
            self.assertEqual(phases,[initial,(initial+4)%16,initial,(initial+8)%16])
            self.assertEqual(phase_sequence([3]*32,increments,initial),
                             [(initial+8)%16,initial]*16)
        with self.assertRaises(ValueError):phase_sequence([4],increments)

    def test_reject_altered_rom_and_search_last_window(self):
        data=bytearray(ROM.read_bytes());data[0x7e]^=1
        with self.assertRaises(ValueError):inspect(data)
        self.assertEqual(occurrences(bytes([9,0,4,12,8]),[0,4,12,8]),[1])


if __name__=='__main__':unittest.main()
