"""Test the fixed ROM 16F–1CF window against RC/RRC pulse families."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROM=HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin'
EXPECTED_SHA='312fa21f50203c7b84ec0a4b4aea62ca343b2a579c38687111342368b1f04d58'
START,END=0x16f,0x1d0


def sinc(x):
    return 1.0 if abs(x)<1e-12 else math.sin(math.pi*x)/(math.pi*x)


def raised_cosine(x,beta):
    denominator=1-(2*beta*x)**2
    if abs(denominator)<1e-10:
        return math.pi/4*sinc(1/(2*beta))
    return sinc(x)*math.cos(math.pi*beta*x)/denominator


def root_raised_cosine(x,beta):
    if abs(x)<1e-12:
        return 1+beta*(4/math.pi-1)
    if abs(abs(x)-1/(4*beta))<1e-10:
        return beta/math.sqrt(2)*((1+2/math.pi)*math.sin(math.pi/(4*beta))+
                                  (1-2/math.pi)*math.cos(math.pi/(4*beta)))
    return (math.sin(math.pi*x*(1-beta))+4*beta*x*math.cos(math.pi*x*(1+beta)))/(
        math.pi*x*(1-(4*beta*x)**2))


def fit(target,template):
    n=len(target);mx=sum(template)/n;my=sum(target)/n
    denominator=sum((v-mx)**2 for v in template)
    if denominator<1e-12:return None
    scale=sum((v-mx)*(w-my) for v,w in zip(template,target))/denominator
    offset=my-scale*mx
    mse=sum((scale*v+offset-w)**2 for v,w in zip(template,target))/n
    return mse,scale,offset


def run():
    image=ROM.read_bytes()
    if len(image)!=512 or hashlib.sha256(image).hexdigest()!=EXPECTED_SHA:
        raise ValueError('Am27S31 dump changed')
    y=[v if v<128 else v-256 for v in image[START:END]]
    mean=sum(y)/len(y);variance=sum((v-mean)**2 for v in y)/len(y)
    best={};at_beta_one={}
    for name,function in [('raised_cosine',raised_cosine),
                          ('root_raised_cosine',root_raised_cosine)]:
        for samples in (4,6,8,12):
            top=None;one=None
            for beta_i in range(1,21):
                beta=beta_i*0.05
                for center_i in range(4*len(y)):
                    center=center_i/4
                    template=[function((i-center)/samples,beta) for i in range(len(y))]
                    result=fit(y,template)
                    if result is None:continue
                    mse,scale,offset=result
                    row=dict(samples_per_symbol=samples,rolloff=round(beta,2),
                             center_index=center,scale=scale,offset=offset,
                             rmse=math.sqrt(mse),r_squared=1-mse/variance)
                    if top is None or mse<top[0]:top=(mse,row)
                    if beta_i==20 and (one is None or mse<one[0]):one=(mse,row)
            best[f'{name}_{samples}']=top[1]
            at_beta_one[f'{name}_{samples}']=one[1]
    return dict(status='scoped numerical fit; no DSP table role inferred',
        rom_sha256=EXPECTED_SHA,window=f'{START:03X}-{END-1:03X}',
        signed_values=y,variance=variance,
        search=dict(samples_per_symbol=[4,6,8,12],rolloff=[0.05,1.0,0.05],
                    center_step=0.25,center_range=[0,len(y)-0.25],
                    amplitude='least-squares free scale and offset'),
        best=best,rolloff_one=at_beta_one,
        limitations=['Only the predetermined contiguous 97-byte window is tested.',
                     'The physical sample rate, table boundaries, scaling and address order are unknown.',
                     'A poor fit does not exclude a polyphase or transformed pulse table.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/pulse-fit.json')
    args=parser.parse_args();report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print({k:round(v['r_squared'],3) for k,v in report['best'].items()})


if __name__=='__main__':main()
