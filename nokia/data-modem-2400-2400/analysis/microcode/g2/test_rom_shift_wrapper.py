"""Check ROM-driven wrapper exit and sensitivity to the read gate."""

import json
import tempfile
import unittest
from pathlib import Path

from rom_shift_wrapper import GATES, MAPPING, SCENARIO, SINE, fixture
from rom_shift_wrapper import read, execute


class RomShiftWrapper(unittest.TestCase):
    def test_fitted_gate_reaches_left_shift_with_zero_rom_byte(self):
        mapping = read(MAPPING)
        source = read(SCENARIO)
        gate = read(GATES)['fits'][61]
        scenario = fixture(source, gate, read(SINE)['rom_sha256'], 256, 128)
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, 1000, seed=6,
                             mode='integrated', out=Path(temporary), trace_limit=300)
            trace = [json.loads(line) for line in (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        self.assertTrue(result['clean'])
        self.assertEqual(result['final_state']['pc'], 0x084)
        self.assertEqual(result['address_counts'][0x24e], 2)
        self.assertEqual(result['address_counts'].get(0x392, 0), 0)
        left = [row for row in trace if row['pc'] == 0x187]
        self.assertEqual([(row['q'], row['external_read']['address'],
                           row['external_read']['value']) for row in left],
                         [(0, 256, 0), (0, 256, 0)])
        first = [row for row in trace if row['pc'] == 0x299][:9]
        self.assertEqual([row['q'] for row in first],
                         [128, 64, 32, 16, 8, 4, 2, 1, 0])

    def test_broader_gate_can_divert_before_wrapper(self):
        mapping = read(MAPPING)
        source = read(SCENARIO)
        gate = read(GATES)['fits'][99]
        scenario = fixture(source, gate, read(SINE)['rom_sha256'], 0, 128)
        result = execute(mapping, scenario, 1000, seed=6,
                         mode='integrated', trace_limit=0)
        self.assertTrue(result['clean'])
        self.assertEqual(result['final_state']['pc'], 0x117)
        self.assertEqual(result['address_counts'].get(0x187, 0), 0)


if __name__ == '__main__':
    unittest.main()
