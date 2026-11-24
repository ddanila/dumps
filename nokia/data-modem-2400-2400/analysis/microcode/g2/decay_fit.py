"""Compare ROM 141–16E with simple affine decay lookup families."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from pulse_fit import ROM, EXPECTED_SHA, fit

HERE=Path(__file__).resolve().parent
START,END=0x141,0x16f


def shape(name,x,t):
    if name=='linear':return float(x)
    if name=='exponential':return math.exp(-x/t)
    if name=='reciprocal':return 1/(x+t)
    if name=='inverse_sqrt':return 1/math.sqrt(x+t)
    if name=='logarithm':return math.log(x+t)
    raise ValueError(name)


def run():
    image=ROM.read_bytes()
    if len(image)!=512 or hashlib.sha256(image).hexdigest()!=EXPECTED_SHA:
        raise ValueError('Am27S31 dump changed')
    y=list(image[START:END]);n=len(y)
    variance=sum((v-sum(y)/n)**2 for v in y)/n
    results={}
    for name in ('linear','exponential','reciprocal','inverse_sqrt','logarithm'):
        best=None
        grid=(1,) if name=='linear' else range(1,1001)
        for ti in grid:
            t=ti/10
            z=[shape(name,i,t) for i in range(n)]
            candidate=fit(y,z)
            if candidate is None:continue
            mse,scale,offset=candidate
            if best is None or mse<best[0]:best=(mse,t,scale,offset,z)
        mse,t,scale,offset,z=best
        predicted=[scale*v+offset for v in z]
        results[name]=dict(shape_parameter=t,scale=scale,offset=offset,
                           rmse=math.sqrt(mse),r_squared=1-mse/variance,
                           rounded_exact=sum(round(v)==actual for v,actual in zip(predicted,y)),
                           max_absolute_error=max(abs(v-actual) for v,actual in zip(predicted,y)))
    return dict(status='scoped shape comparison, no DSP table role established',
        rom_sha256=EXPECTED_SHA,window=f'{START:03X}-{END-1:03X}',
        unsigned_values=y,following_signed_byte=image[END]-256,
        search=dict(parameter_grid='0.1 to 100.0 in steps of 0.1; linear has no parameter',
                    amplitude='least-squares free scale and offset'),fits=results,
        interpretation='The 46-byte descending segment is closer to an affine exponential than a line; reciprocal and other smooth decays are nearly as good. No candidate is an exact rounded match.',
        limitations=['The segment boundary is chosen from the visible discontinuity at 16F.',
                     'These flexible smooth curves are not specific signatures of an AGC or filter algorithm.',
                     'ROM address wiring and the microcode consumer are unverified.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/decay-fit.json')
    args=parser.parse_args()
    report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print({name:(round(row['r_squared'],4),row['rounded_exact'])
           for name,row in report['fits'].items()})


if __name__=='__main__':main()
