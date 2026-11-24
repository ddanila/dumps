import unittest

from all_rom_gate_cycles import run


class AllRomGateCycles(unittest.TestCase):
    def test_all_fitted_gates_miss_paired_output_d_bus(self):
        report=run()
        self.assertEqual(report['gate_fit_count'],137)
        self.assertEqual(report['fits_without_cyclic_d'],73)
        self.assertEqual(report['fits_with_d_in_paired_output_loop'],0)
        self.assertEqual(report['cyclic_d_sites_with_register_write'],
                         ['1EC','36C','36E'])
        self.assertEqual(set(report['by_mapping']),
                         {'q1','q2','q3','q4','fitted_original','fitted_swapped'})
        for mapping in report['by_mapping'].values():
            self.assertEqual(mapping['cyclic_d_register_writes'],
                             {'1EC':18,'36C':25,'36E':10})


if __name__=='__main__':unittest.main()
