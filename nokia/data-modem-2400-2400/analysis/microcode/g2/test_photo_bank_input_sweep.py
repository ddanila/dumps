"""Check the bounded early-D input screen against both ROM bank hypotheses."""
import tempfile
import unittest
from pathlib import Path

from photo_bank_input_sweep import run


class PhotoBankInputSweepTest(unittest.TestCase):
    def test_all_early_bytes_leave_the_same_control_outcome_per_bank(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        lower, upper = report['cases']
        self.assertEqual((lower['bank_12c'], upper['bank_12c']), (0, 256))
        self.assertEqual((lower['final_pcs'], upper['final_pcs']),
                         ({'084': 256}, {'12D': 256}))
        self.assertEqual((lower['visits_12c'], upper['visits_12c']),
                         ({1: 256}, {52: 256}))
        for case in report['cases']:
            self.assertEqual(case['clean_count'], 256)
            self.assertEqual(case['distinct_final_ram_q'], 1)
            self.assertEqual(case['distinct_trace_digests'], 256)
            self.assertEqual(case['phase_map_inputs'], [])
            self.assertEqual(case['candidate_output_site_inputs'], [])
        self.assertEqual([(row['input'], row['external_read']['value'],
                           row['external_read']['selected_by_alu'], row['alu']['f'])
                          for row in report['witnesses']],
                         [(value, value, True, value) for value in (0, 165, 255)])


if __name__ == '__main__':
    unittest.main()
