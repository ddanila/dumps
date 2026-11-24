"""Receiver-stimulus regression for the photo-constrained D38E candidate."""
import tempfile
import unittest
from pathlib import Path

from adc_sample_path import run


class AdcSamplePathTest(unittest.TestCase):
    def test_complementary_reference_samples_do_not_create_history_in_this_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run(Path(temporary))
        self.assertEqual(result['reference_receive_errors'], 0)
        self.assertTrue(result['same_byte_state_order_invariant'])
        self.assertEqual(len(result['cases']), 4)
        for case in result['cases']:
            self.assertTrue(case['clean'])
            self.assertEqual((case['samples'], case['distinct_input_codes'],
                              case['max_states_per_code'],
                              case['post_dispatch_rom_reads']), (256, 72, 1, 0))
            self.assertEqual(case['output_groups_by_code_mod4'], {
                '0': [[11, 11, 6, 6]],
                '1': [[11, 11, 16, 16]],
                '2': [[1, 1, 6, 6]],
                '3': [[1, 1, 252, 251]],
            })


if __name__ == '__main__':
    unittest.main()
