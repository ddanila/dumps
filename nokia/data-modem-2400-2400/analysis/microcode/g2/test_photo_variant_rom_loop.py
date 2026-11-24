"""Regression checks for the real-PROM photo-variant ROM feedback run."""
import tempfile
import unittest
from pathlib import Path

from photo_variant_rom_loop import run


class PhotoVariantRomLoopTest(unittest.TestCase):
    def test_q1_sustains_the_same_measured_recurrence_under_all_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        q1 = [case for case in report['cases'] if case['mapping'] == 'q1']
        q2 = [case for case in report['cases'] if case['mapping'] == 'q2']
        self.assertEqual((len(q1), len(q2)), (16, 16))
        for case in q1:
            site = case['sites']['12C']
            self.assertEqual((site['visits'], site['rom_reads']), (500, 500))
            self.assertTrue(site['address_is_prev_y_plus_one_upper_bank'])
            self.assertEqual((site['recurrence']['preperiod'],
                              site['recurrence']['period'],
                              site['recurrence']['exact_to_end']), (8, 20, True))
            self.assertGreater(site['distinct_alu_y'], 16)
        self.assertTrue(all(case['sites']['12C']['recurrence']['period'] != 20
                            for case in q2))
        self.assertEqual([(case['value'], case['first_blt_next_pc'])
                          for case in report['zero_exit_probe']],
                         [(0, '130'), (1, '12C')])
        cycle_basins = [basin for basin in report['rom_feedback_basins']['256']
                        if basin['kind'] == 'cycle']
        self.assertEqual(len(cycle_basins), 1)
        self.assertEqual((len(cycle_basins[0]['cycle_values']),
                          len(cycle_basins[0]['seeds'])), (20, 245))
        lower = report['rom_feedback_basins']['0']
        self.assertTrue(all(basin['kind'] == 'zero' for basin in lower))
        self.assertEqual(sum(len(basin['seeds']) for basin in lower), 256)
        self.assertLessEqual(max(basin['steps_to_zero'] for basin in lower), 10)
        self.assertEqual((report['lower_bank_probe']['first_rom_address'],
                          report['lower_bank_probe']['first_rom_value'],
                          report['lower_bank_probe']['first_blt_next_pc']),
                         (255, 0, '130'))


if __name__ == '__main__':
    unittest.main()
