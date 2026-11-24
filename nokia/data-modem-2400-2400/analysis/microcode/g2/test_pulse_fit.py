import math
import unittest

from pulse_fit import fit, raised_cosine, root_raised_cosine, run


class PulseFit(unittest.TestCase):
    def test_synthetic_pulse_and_singular_limits(self):
        template=[raised_cosine((i-48)/8,1) for i in range(97)]
        target=[13*x+2 for x in template]
        mse,scale,offset=fit(target,template)
        self.assertLess(mse,1e-25)
        self.assertAlmostEqual(scale,13)
        self.assertAlmostEqual(offset,2)
        for x in (0,0.25,0.5,-0.25,-0.5):
            self.assertTrue(math.isfinite(raised_cosine(x,1)))
            self.assertTrue(math.isfinite(root_raised_cosine(x,1)))

    def test_fixed_dump_window_is_not_a_simple_pulse(self):
        report=run()
        self.assertEqual(len(report['signed_values']),97)
        self.assertLess(max(x['r_squared'] for x in report['best'].values()),0.4)


if __name__=='__main__':unittest.main()
