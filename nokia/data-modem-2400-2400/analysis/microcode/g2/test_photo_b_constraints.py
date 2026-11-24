from copy import deepcopy
import tempfile
import unittest
from pathlib import Path

from photo_b_constraints import ASSUMED, HERE, check_mapping, read, save, swapped
from photo_hypotheses import candidate


class PhotoBConstraints(unittest.TestCase):
    def setUp(self):
        self.constraints = read(HERE / 'photo-b-constraints.json')
        self.catalog = read(ASSUMED / 'program-reading.json')['profiles']

    def test_lane_constraint_separates_existing_register_roles(self):
        compatible = []
        for name, path in self.catalog.items():
            mapping = read(ASSUMED / path)
            if check_mapping(mapping, self.constraints)['lane_compatible']:
                compatible.append(name)
        self.assertEqual(compatible, ['fitted_swapped'])

    def test_unknown_register_permutation_does_not_become_exact_bit_evidence(self):
        mapping = read(ASSUMED / self.catalog['fitted_swapped'])
        mapping['fields']['b']['bits'][1:3] = reversed(mapping['fields']['b']['bits'][1:3])
        result = check_mapping(mapping, self.constraints)
        self.assertTrue(result['lane_compatible'])
        self.assertFalse(result['identity_permutation_match'])

    def test_new_mapping_changes_runtime_wiring_without_mutating_source(self):
        original = read(ASSUMED / self.catalog['q3'])
        before = deepcopy(original)
        mapping = swapped(original)
        self.assertEqual(original, before)
        self.assertEqual(mapping['fields']['i'], original['fields']['i'])
        self.assertTrue(check_mapping(mapping, self.constraints)['lane_compatible'])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'mapping.json'
            save(path, mapping)
            actual = candidate('q3-photo-swapped', mapping_path=path)
            previous = candidate('q3')
            for chip in ('U2', 'U8'):
                self.assertEqual(actual['components'][chip]['inputs']['B'],
                                 previous['components'][chip]['inputs']['A'])
                self.assertEqual(actual['components'][chip]['inputs']['A'],
                                 previous['components'][chip]['inputs']['B'])


if __name__ == '__main__':
    unittest.main()
