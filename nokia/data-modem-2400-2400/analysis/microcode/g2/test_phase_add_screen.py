import unittest

from phase_add_screen import cyclic_components, run


class PhaseAddScreen(unittest.TestCase):
    def test_stack_state_cycles(self):
        a=(1,(7,));b=(2,(7,));c=(3,());d=(4,())
        cycles=cyclic_components([(a,b),(b,a),(b,c),(c,d),(d,d)])
        self.assertEqual({frozenset(x) for x in cycles},
                         {frozenset((a,b)),frozenset((d,))})

    def test_declared_q3_graph_has_no_direct_accumulator_cycle(self):
        result=run()
        self.assertEqual(result['control_flow']['direct_accumulators_in_cycles'],[])
        self.assertGreater(result['control_flow']['cyclic_component_count'],0)


if __name__=='__main__':unittest.main()
