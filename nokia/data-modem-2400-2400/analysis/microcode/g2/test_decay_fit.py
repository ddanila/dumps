import unittest

from decay_fit import run, shape


class DecayFitTest(unittest.TestCase):
    def test_segment_boundary_and_nonunique_decay(self):
        report=run()
        self.assertEqual(report['window'],'141-16E')
        self.assertEqual(report['following_signed_byte'],-8)
        self.assertEqual(len(report['unsigned_values']),46)
        fits=report['fits']
        self.assertGreater(fits['exponential']['r_squared'],fits['linear']['r_squared'])
        self.assertLess(fits['exponential']['r_squared']-fits['reciprocal']['r_squared'],0.01)
        self.assertLess(fits['exponential']['rounded_exact'],46)

    def test_shape_families_have_expected_monotonicity(self):
        for name in ('exponential','reciprocal','inverse_sqrt'):
            self.assertGreater(shape(name,0,20),shape(name,45,20))
        self.assertLess(shape('logarithm',0,20),shape('logarithm',45,20))


if __name__=='__main__':unittest.main()
