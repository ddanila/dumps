import unittest

from c2_bridge_check import run


class C2BridgeCheck(unittest.TestCase):
    def test_saved_bridge_fails_changing_sample_gate(self):
        report=run()
        self.assertEqual(report['reference']['steady_1800_hz_peak']['frequency_hz'],1800)
        self.assertGreater(report['reference']['distinct_pcm_codes'],1)
        for candidate in report['candidates'].values():
            self.assertEqual(candidate['transfer_count'],17)
            self.assertEqual(candidate['centered_sample_energy'],0)
            self.assertFalse(candidate['c2_changing_sample_gate'])


if __name__=='__main__':unittest.main()
