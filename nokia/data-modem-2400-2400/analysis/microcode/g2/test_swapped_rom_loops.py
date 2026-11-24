"""Regression checks for executable photo-compatible ROM-loop candidates."""
import tempfile
import unittest
from pathlib import Path

from swapped_sine_loop import run as run_q3
from swapped_q2_rom_loop import run as run_q2


class SwappedRomLoops(unittest.TestCase):
    def test_q3_sine_input_changes_across_fixtures_but_not_within_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run_q3(Path(temporary))
        self.assertEqual(report['tested_phases'], list(range(65)))
        self.assertEqual(len(report['repeated_phases']), 64)
        self.assertEqual(report['changing_output_phases'], [])
        self.assertEqual(report['outcomes'][32]['first_output_group'], [0, 0, 190, 64])
        self.assertEqual(report['outcomes'][32]['output_group_periods'], [12])
        self.assertEqual(report['outcomes'][32]['distinct_q_at_output'], 1)
        self.assertEqual([r['pc'] for r in report['outcomes'][32]['rom_reads']],
                         ['115', '115', '317'])
        self.assertEqual(report['zero_317_control']['first_output_group'], [0, 0, 10, 64])
        self.assertEqual(report['zero_317_control']['complete_output_groups'], 81)

    def test_q2_rom_fed_loop_stabilizes_under_every_repeating_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run_q2(Path(temporary))
        self.assertEqual(report['candidate_gate_count'], 16)
        repeating = [c for c in report['cases'] if c['visits_127'] > 1]
        self.assertEqual(len(repeating), 8)
        for case in repeating:
            self.assertEqual(case['visits_127'], 118)
            self.assertEqual(case['selected_reads_127'], 118)
            self.assertEqual(len(set(case['last_16_y'])), 1)
            self.assertEqual(case['q_127'], [0])
            self.assertGreater(len(case['addresses_127']), 1)
        self.assertEqual(report['repeated_12c_gate_count'], 4)
        for case in (c for c in report['cases'] if c['visits_12c'] > 1):
            self.assertEqual(case['visits_12c'], 116)
            self.assertEqual(case['selected_reads_12c'], 116)
            self.assertEqual(case['addresses_12c'], [257, 511])
            self.assertEqual(case['values_12c'], [3, 11])
            self.assertEqual(set(case['last_16_y_12c']), {3})


if __name__ == '__main__':
    unittest.main()
