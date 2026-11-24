"""Compare the saved diagnostic q3 DAC bridge with C2 transmit signatures."""
import argparse
import hashlib
import json
from pathlib import Path

from reference_modem import spectral_peak, transmit

HERE=Path(__file__).resolve().parent
ASSUMED=HERE.parent/'assumed'
NAMES=('frame-05','frame-85')


def run():
    reference=transmit([0]*80)
    reference_peak=spectral_peak(reference)
    assert reference_peak['frequency_hz']==1800
    candidates={};digests={}
    for name in NAMES:
        path=ASSUMED/'results/frame-dac-bridge'/name/'dac.json'
        digests[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        events=json.loads(path.read_text())['events']
        transfers=[e for e in events if e['action']=='transfer-open']
        cycles=[e['cycle'] for e in transfers]
        codes=[e['dac_register'] for e in transfers]
        assert cycles==[55+12*i for i in range(17)]
        assert len(set(codes))==1 and all(e['pc']==0x392 for e in transfers)
        candidates[name]=dict(transfer_count=len(codes),cycles=cycles,
                              codes=codes,distinct_codes=len(set(codes)),
                              centered_sample_energy=sum((x-sum(codes)/len(codes))**2 for x in codes),
                              c2_changing_sample_gate=False)
    return dict(status='both saved diagnostic bridge paths fail C2 changing-sample gate',
        reference=dict(steady_1800_hz_peak=reference_peak,
                       distinct_pcm_codes=len(set(reference))),
        candidates=candidates,source_sha256=digests,
        interpretation='Under the declared q3 bridge and DAC strobe hypothesis, each controller frame produces 17 transfers of one held code. Such a sequence has zero AC sample energy and cannot show the required carrier or dibit phase steps.',
        limitations=['The bridge input routing and DAC strobes are explicit hypotheses, not traced board nets.',
                     'Only the two saved controller fixtures and their 256-instruction microcode runs are compared.',
                     'The bridge study separately checked the repeating 12-instruction full-state recurrence.',
                     'Failure of this candidate does not rule out a different mapping, entry, output site or physical sample clock.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/c2-bridge-check.json')
    args=parser.parse_args();report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'])


if __name__=='__main__':main()
