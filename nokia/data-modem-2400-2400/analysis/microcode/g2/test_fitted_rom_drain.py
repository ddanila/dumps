"""Check the photo-compatible fitted mapping's ROM-fed 299 path."""
import tempfile
import unittest
from pathlib import Path

from fitted_rom_drain import run


class FittedRomDrain(unittest.TestCase):
    def test_all_299_gates_are_finite_and_miss_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        self.assertEqual(report['candidate_gate_count'], 48)
        self.assertEqual({int(k): v for k, v in report['visit_distribution'].items()},
                         {2: 18, 3: 18, 4: 4, 5: 8})
        self.assertTrue(all(c['clean'] and c['visits_output_392'] == 0
                            for c in report['cases']))
        witness = report['cases'][0]['selected_reads_299']
        self.assertEqual([r['address'] for r in witness], [510, 383, 319])
        self.assertEqual([r['q'] for r in witness], [254, 127, 63])
        self.assertEqual([r['value'] for r in witness], [10, 8, 127])


if __name__ == '__main__':
    unittest.main()
