"""Regression for the scoped q1 05D–063 ROM-read candidate."""
import tempfile
import unittest
from pathlib import Path

from photo_05d_loop import run


class Photo05dLoopTest(unittest.TestCase):
    def test_reset_reachability_and_stationary_local_lookup(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        self.assertEqual(report['gate_index'], 47)
        self.assertEqual(len(report['cases']), 2)
        for case in report['cases']:
            self.assertEqual(case['reset_reached_q'], [])
            self.assertEqual(case['local_clean'], 256)
            self.assertEqual(case['local_final_pcs'], {'084': 1, '05F': 255})
            self.assertEqual(case['local_q_changes'], [])
        for row in report['witnesses']:
            q = row['initial_q']
            self.assertEqual(row['final_q'], q)
            self.assertEqual(row['sites']['05E']['address'],
                             row['bank'] + ((q + 1) & 255))
            self.assertEqual(row['sites']['05E']['rom_value'],
                             row['sites']['061']['rom_value'])
            self.assertEqual(row['sites']['05E']['alu_y'],
                             row['sites']['061']['alu_y'])


if __name__ == '__main__':
    unittest.main()
