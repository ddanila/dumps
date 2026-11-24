import unittest

from reference_modem import (echo_cancel, phase_positions, receive, run,
                             spectral_peak, transmit)


class ReferenceModem(unittest.TestCase):
    def test_differential_map_all_dibits(self):
        dibits=[0,1,2,3]*16
        phases=phase_positions(dibits)
        increments=[(phases[0]-0)&15]+[(b-a)&15 for a,b in zip(phases,phases[1:])]
        self.assertEqual(increments,[0,4,12,8]*16)

    def test_pcm_receive_and_carrier(self):
        dibits=[0]*8+[0,1,3,2,2,3,1,0]*8+[0]*8
        pcm=transmit(dibits)
        self.assertEqual(receive(pcm),dibits[1:])
        self.assertEqual(spectral_peak(transmit([0]*80))['frequency_hz'],1800)

    def test_echo_training_freezes(self):
        reference=transmit([0,1,2,3]*32)
        echo=[round(0.6*(reference[n-3] if n>=3 else 0))
              for n in range(len(reference))]
        result=echo_cancel(reference,echo,train_until=512)
        self.assertEqual(result['weights_q15'],result['frozen_weights_q15'])
        self.assertLess(sum(x*x for x in result['residual'][256:512]),
                        sum(x*x for x in result['residual'][32:288]))

    def test_report_is_reference_only(self):
        report=run()
        self.assertEqual(report['receive']['errors'],0)
        self.assertIn('no DSC2847 execution',report['status'])


if __name__=='__main__':unittest.main()
