"""Verify that a scenario-supplied instruction line changes the real-ROM run."""
import tempfile
import unittest
from pathlib import Path

from photo_i7_control import run


class PhotoI7ControlTest(unittest.TestCase):
    def test_fixed_levels_remove_q3_candidate_output_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            rows = run(Path(temporary))['cases']
        self.assertEqual(rows[0]['input_38e_visits'], 39)
        self.assertEqual(rows[0]['candidate_output_word_visits'], 156)
        for row in rows[1:]:
            self.assertTrue(row['clean'])
            self.assertEqual(row['input_38e_visits'], 0)
            self.assertEqual(row['candidate_output_word_visits'], 0)
            self.assertEqual(row['final_pc'], '084')
        self.assertNotEqual(rows[1]['trace_digest'], rows[2]['trace_digest'])


if __name__ == '__main__':
    unittest.main()
