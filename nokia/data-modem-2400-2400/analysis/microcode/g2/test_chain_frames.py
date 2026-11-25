import unittest

from chain_frames import run


class ChainFramesTest(unittest.TestCase):
    def test_preserved_ram_state_and_frame_branches(self):
        report=run()
        self.assertEqual(len(report['rows']),256)
        self.assertEqual(report['distinct_chains'],4)
        for row in report['rows']:
            value=int(row['selector'],16)
            steps=row['steps']
            self.assertEqual([s['after'] for s in steps[:2]],['A1','A2'])
            self.assertEqual([s['wire'] for s in steps[:2]],
                             ['80 02 81 7A','80 02 88 7A'])
            self.assertEqual([int(s['p1'],16)&0x20 for s in steps[:2]],[0,0])
            self.assertEqual(steps[2]['after'],'A3' if value&0x40 else 'B8')
            self.assertEqual(steps[2]['wire'],
                             f'{"C0" if value&1 else "D0"} 42 81 {"BA" if value&0x40 else "22"}')
            self.assertEqual(steps[3]['after'],'A4' if value&0x40 else 'B4')


if __name__=='__main__': unittest.main()
