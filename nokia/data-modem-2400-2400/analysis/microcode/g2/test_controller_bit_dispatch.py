"""End-to-end regression for controller-ROM bits through candidate microcode dispatch."""
import tempfile
import unittest
from pathlib import Path

from controller_bit_dispatch import run


class ControllerBitDispatch(unittest.TestCase):
    def test_real_controller_scrambler_bits_select_but_do_not_modulate(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(Path(temporary))
        self.assertEqual(report['scrambled_bytes'][:4], [0x38, 0x69, 0x86, 0x38])
        self.assertEqual(report['bit_count'], 128)
        self.assertEqual(len(report['controller_groups']), 128)
        self.assertEqual([g['index'] for g in report['controller_groups']], report['bits'])
        self.assertEqual({g['first_pc'] for g in report['controller_groups']}, {'392', '396'})
        self.assertTrue(all(g['bytes'] == [0, 0, 190, 64]
                            for g in report['controller_groups']))
        self.assertTrue(report['output_equal_to_zero_control'])
        self.assertEqual(report['post_group_state_count'], 128)
        self.assertEqual(report['distinct_post_group_states'], 1)
        self.assertTrue(report['post_group_states_equal_to_zero_control'])
        self.assertNotEqual(report['controller_trace_digest'], report['zero_trace_digest'])
        self.assertTrue(all(row['equal'] for row in report['phase_comparison']))
        self.assertEqual([row['first_entry']['first_pc'] for row in report['four_way']],
                         ['392', '396', '39A', '39E'])
        self.assertEqual([row['entry_count'] for row in report['four_way']],
                         [81, 81, 1, 1])


if __name__ == '__main__':
    unittest.main()
