import unittest

from rom_cycle_screen import run


class RomCycleScreen(unittest.TestCase):
    def test_declared_gate_has_only_three_cycle_shapes(self):
        report=run()
        self.assertEqual({tuple(row['cyclic_pcs']) for row in report['rom_d_cycle_shapes']},
                         {('02B','02C','02D','02E'),('1EC','1ED'),('36C','36D','36E')})
        self.assertEqual(sum(row['component_count'] for row in report['rom_d_cycle_shapes']),5)


if __name__=='__main__':unittest.main()
