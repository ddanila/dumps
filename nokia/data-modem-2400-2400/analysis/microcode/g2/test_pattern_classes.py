import unittest

from pattern_classes import run


class PatternClassesTest(unittest.TestCase):
    def test_real_rom_state_dependent_classes(self):
        groups=run()['groups']
        singles=['01','02','04','08','10','20','40','80']
        pairs=['03','06','0C','18','30','60','81','C0']
        self.assertEqual(groups['83']['04'],singles)
        self.assertEqual(groups['A6']['04'],singles)
        self.assertEqual(groups['A6']['08'],pairs)
        self.assertEqual(groups['83']['0C'],['07','0E','1C','38','70','83','C1','E0'])
        for classes in groups.values():
            marked=[v for group in classes.values() for v in group]
            self.assertEqual(len(marked),256)
            self.assertEqual(len(set(marked)),256)


if __name__=='__main__':unittest.main()
