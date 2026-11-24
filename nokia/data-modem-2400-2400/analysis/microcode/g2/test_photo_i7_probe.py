"""Regression check for the photo-I7 candidate's control-flow effect."""
import tempfile
import unittest
from pathlib import Path

from photo_i7_probe import run


class PhotoI7ProbeTest(unittest.TestCase):
    def test_identity_bit_order_redirects_q3_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            cases = {row['label']: row for row in run(Path(temporary))['cases']}
        self.assertEqual(cases['baseline']['input_38e_visits'], 39)
        self.assertEqual(cases['baseline']['candidate_output_word_visits'], 156)
        for name in ('identity', 'inverted_identity'):
            self.assertTrue(cases[name]['clean'])
            self.assertEqual(cases[name]['input_38e_visits'], 0)
            self.assertEqual(cases[name]['candidate_output_word_visits'], 0)
            self.assertEqual(cases[name]['final_pc'], '084')


if __name__ == '__main__':
    unittest.main()
