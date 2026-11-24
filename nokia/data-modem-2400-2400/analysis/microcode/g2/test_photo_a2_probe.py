"""Check that the photo A2 candidate is screened and reaches the real-ROM run."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from photo_a2_probe import SCENARIO, read, run
from execute import validate_scenario


class PhotoA2ProbeTest(unittest.TestCase):
    def test_a2_candidate_changes_mapping_but_not_q3_dispatch_in_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        self.assertTrue(all(bit != '10.7' for bit in report['existing_a2'].values()))
        cases = {(row['a2'], str(row['i7']), str(row['a0'])): row for row in report['cases']}
        self.assertEqual(cases[('17.7', 'PROM-bit baseline', 'PROM-bit baseline')]['input_38e_visits'], 39)
        self.assertEqual(cases[('10.7', 'PROM-bit baseline', 'PROM-bit baseline')]['input_38e_visits'], 39)
        for a2 in ('17.7', '10.7'):
            for level in ('0', '1'):
                case = cases[(a2, level, level)]
                self.assertTrue(case['clean'])
                self.assertEqual(case['input_38e_visits'], 0)
                self.assertEqual(case['final_pc'], '084')
        self.assertNotEqual(cases[('17.7', '1', '1')]['trace_digest'],
                            cases[('10.7', '1', '1')]['trace_digest'])

    def test_address_override_requires_provenance_and_valid_bit(self):
        scenario = read(SCENARIO)
        for bit, policy in (('0', {'value': 1}),
                            ('4', {'value': 1, 'status': 'hypothesis', 'evidence': 'test'})):
            fixture = deepcopy(scenario)
            fixture['inputs']['register_address_bit_overrides'] = {'a': {bit: policy}}
            with self.assertRaises(ValueError):
                validate_scenario(fixture)


if __name__ == '__main__':
    unittest.main()
