import unittest

from sequence_alignment import run


class SequenceAlignment(unittest.TestCase):
    def test_nominal_matches_but_reload_only_has_two_near_misses(self):
        report=run()
        self.assertEqual(len(report['rows']),7)
        self.assertTrue(all(row['nominal_in_window'] for row in report['rows']))
        self.assertEqual({row['state'] for row in report['rows']
                          if not row['raw_in_window']},{'A0','A1'})
        self.assertLess(report['timer']['raw_reload_to_overflow_ms'],1)


if __name__=='__main__':unittest.main()
