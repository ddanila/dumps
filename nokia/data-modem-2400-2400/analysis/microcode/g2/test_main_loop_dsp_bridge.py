"""Check controller-ROM bytes through the photo candidate DSC2847 dispatch."""

import tempfile
import unittest
from pathlib import Path

from main_loop_dsp_bridge import run


class MainLoopDspBridge(unittest.TestCase):
    def test_real_controller_streams_do_not_advance_candidate_phase(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        self.assertEqual([case['stream'] for case in report['cases']],
                         ['00', '20', '40', '60', 'combined'])
        self.assertEqual([case['bits'] for case in report['cases']],
                         [64, 64, 48, 48, 224])
        for case in report['cases']:
            self.assertTrue(case['clean'])
            self.assertEqual(case['input_reads'], case['bits'])
            self.assertEqual(case['dispatch_groups'], case['bits'])
            self.assertEqual(case['group_by_bit'],
                             {'0': [[11, 11, 6, 6]], '1': [[11, 11, 16, 16]]})
            self.assertEqual(case['distinct_post_group_states_by_bit'],
                             {'0': 1, '1': 1})
            self.assertEqual(case['later_rom_reads'], 0)
            self.assertEqual(case['final_q'], 5)
        self.assertEqual(report['cases'][-1]['candidate_output_word_392'], 117)


if __name__ == '__main__':
    unittest.main()
