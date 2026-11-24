"""Check the uninterrupted controller loop's A2 branch and output dependence."""

import unittest

from main_loop_chain import run


class MainLoopChain(unittest.TestCase):
    def test_received_selector_controls_main_loop_branch_and_frames(self):
        report = run()
        self.assertEqual(len(report['rows']), 256)
        self.assertEqual(report['distinct_chains'], 6)
        for row in report['rows']:
            selector = int(row['selector'], 16)
            steps = row['iterations']
            expected_later = 0xA3 if selector & 0x40 else 0xB8
            expected_after = 0xA4 if selector & 0x40 else 0xB4
            self.assertEqual([s['state'] for s in steps],
                             [0xA1, 0xA1, 0xA2, 0xA2,
                              expected_later, expected_later,
                              expected_after, expected_after])
            self.assertEqual([s['tx'] for s in steps[:4]],
                             [[0x80, 0x02, 0xA1, 0x7A]] * 2 +
                             [[0x80, 0x02, 0xA8, 0x7A]] * 2)
            first = 0xC0 if selector & 1 else 0xD0
            if selector & 0x40:
                second, fourth, later_fourth = 0x42, 0xBA, 0xBA
            else:
                second = 0x42 if selector & 2 and not selector & 8 else 0x47
                fourth, later_fourth = 0x22, 0xEA
            self.assertEqual([s['tx'] for s in steps[4:]],
                             [[first, second, 0xA1, fourth]] * 2 +
                             [[first, second, 0xA1, later_fourth]] * 2)


if __name__ == '__main__':
    unittest.main()
