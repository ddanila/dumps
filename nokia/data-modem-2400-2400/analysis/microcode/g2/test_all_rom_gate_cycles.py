import unittest

from all_rom_gate_cycles import cyclic_write_counts, run, selected_d_pcs


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
        common={'1EC':18,'36C':25,'36E':10}
        for name in ('q3','q4'):
            self.assertEqual(report['by_mapping'][name]['cyclic_d_register_writes'],common)
        for name in ('q1','q2'):
            self.assertEqual(report['by_mapping'][name]['cyclic_d_register_writes'],
                             {**common,'05E':58,'061':22,'127':16,'12C':16})
        for name in ('fitted_original','fitted_swapped'):
            self.assertEqual(report['by_mapping'][name]['cyclic_d_register_writes'],
                             {**common,'187':12,'299':48,'29B':36,'29C':24})

    def test_operand_selection_uses_current_decode_not_cached_fit(self):
        fit={'pcs':[0,1], 'd_selected_pcs':[0]}
        first=[{'i':7 | (3<<6)}, {'i':4 | (3<<6)}]
        second=[{'i':4 | (3<<6)}, {'i':7 | (3<<6)}]
        self.assertEqual(selected_d_pcs(first, fit['pcs']), {0})
        self.assertEqual(selected_d_pcs(second, fit['pcs']), {1})
        self.assertEqual(cyclic_write_counts(second, [fit], {0,1}), {'001':1})

    def test_d_selected_shift_destinations_also_write_state(self):
        rows=[{'i':7 | (destination<<6)} for destination in range(8)]
        counts=cyclic_write_counts(rows,[{'pcs':list(range(8))}],set(range(8)))
        self.assertEqual(set(counts), {'000','002','003','004','005','006','007'})


if __name__=='__main__':unittest.main()
