"""Check continuous 8031 line bytes against state and scrambler expectations."""

import unittest

from main_loop_serial import run


class MainLoopSerial(unittest.TestCase):
    def test_ready_status_produces_four_verified_line_streams(self):
        report = run()
        self.assertEqual(len(report['rows']), 256)
        self.assertEqual(report['distinct_streams'], 4)
        examples = {
            '00': (18, [0, 0, 255, 255, 255, 255, 255, 255],
                   [6, 248, 132, 28, 144, 207, 177, 9]),
            '20': (5, [0, 0, 255, 255, 255, 255, 255, 255],
                   [231, 123, 151, 222, 121, 219, 107, 142]),
            '40': (18, [255] * 6, [249, 7, 248, 28, 28, 240]),
            '60': (5, [255] * 6, [248, 7, 248, 156, 15, 194]),
        }
        rows = {row['selector']: row for row in report['rows']}
        for selector, (delay, sources, output) in examples.items():
            row = rows[selector]
            self.assertEqual((row['delay'], row['line_sources'], row['line_bytes']),
                             (delay, sources, output))
        self.assertEqual(sorted(len(g['selectors']) for g in report['groups']),
                         [32, 32, 96, 96])


if __name__ == '__main__':
    unittest.main()
