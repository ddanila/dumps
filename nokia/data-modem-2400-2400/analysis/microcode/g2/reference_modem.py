"""Small, separate V.26ter-class reference signatures; not DSC2847 execution."""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
SAMPLE_RATE=9600
SYMBOL_RATE=1200
SAMPLES_PER_SYMBOL=8
CARRIER_HZ=1800
TONE_HZ=2100
PHASE_STEPS=(0,4,12,8)  # dibits 00,01,10,11 in 16-position phase
QUADRANT_TO_DIBIT=(0,1,3,2)


def phase_positions(dibits,initial=0):
    phase=initial;result=[]
    for dibit in dibits:
        if dibit not in range(4):raise ValueError('dibit out of range')
        phase=(phase+PHASE_STEPS[dibit])&15
        result.append(phase)
    return result


def sinc(x):
    return 1.0 if abs(x)<1e-12 else math.sin(math.pi*x)/(math.pi*x)


def raised_cosine(x):
    denominator=1-4*x*x
    if abs(denominator)<1e-10:return math.pi/4*sinc(0.5)
    return sinc(x)*math.cos(math.pi*x)/denominator


def transmit(dibits):
    """100%-rolloff symbol pulse, 1800 Hz carrier, signed 8-bit PCM."""
    phases=phase_positions(dibits)
    symbols=[complex(math.cos(math.pi*p/8),math.sin(math.pi*p/8)) for p in phases]
    pcm=[]
    for n in range(len(symbols)*SAMPLES_PER_SYMBOL):
        center=n//SAMPLES_PER_SYMBOL
        base=sum(symbols[k]*raised_cosine((n-8*k)/8)
                 for k in range(max(0,center-4),min(len(symbols),center+5)))
        carrier=complex(math.cos(2*math.pi*CARRIER_HZ*n/SAMPLE_RATE),
                        math.sin(2*math.pi*CARRIER_HZ*n/SAMPLE_RATE))
        pcm.append(max(-127,min(127,round(127*(base*carrier).real))))
    return pcm


def answer_tone(samples):
    return [round(127*math.sin(2*math.pi*TONE_HZ*n/SAMPLE_RATE))
            for n in range(samples)]


def receive(pcm):
    """Known-carrier matched-filter diagnostic, then differential decisions."""
    symbols=len(pcm)//SAMPLES_PER_SYMBOL
    estimates=[]
    for k in range(symbols):
        acc=0j
        for n in range(max(0,8*k-32),min(len(pcm),8*k+33)):
            carrier=complex(math.cos(-2*math.pi*CARRIER_HZ*n/SAMPLE_RATE),
                            math.sin(-2*math.pi*CARRIER_HZ*n/SAMPLE_RATE))
            acc+=pcm[n]*carrier*raised_cosine((n-8*k)/8)
        estimates.append(acc)
    dibits=[]
    for previous,current in zip(estimates,estimates[1:]):
        delta=current*previous.conjugate()
        if abs(delta)<1e-12:raise ValueError('no carrier for differential decision')
        quadrant=min(range(4),key=lambda q:abs(delta/abs(delta)-
                     complex(math.cos(math.pi*q/2),math.sin(math.pi*q/2))))
        dibits.append(QUADRANT_TO_DIBIT[quadrant])
    return dibits


def spectral_peak(pcm,lower=1000,upper=2600):
    """Exact DFT-bin peak, enough for the reference's deterministic fixtures."""
    count=len(pcm)
    bins=range(math.ceil(lower*count/SAMPLE_RATE),
               math.floor(upper*count/SAMPLE_RATE)+1)
    def power(index):
        re=sum(v*math.cos(2*math.pi*index*n/count) for n,v in enumerate(pcm))
        im=sum(v*math.sin(2*math.pi*index*n/count) for n,v in enumerate(pcm))
        return re*re+im*im
    best=max(bins,key=power)
    return dict(frequency_hz=best*SAMPLE_RATE/count,power=power(best),
                bin_width_hz=SAMPLE_RATE/count)


def echo_cancel(reference,echo,taps=8,step_q15=8192,train_until=None):
    """Integer normalized LMS with Q15 taps and frozen coefficients on command."""
    weights=[0]*taps;history=[0]*taps;residual=[];frozen=None
    if train_until is None:train_until=len(reference)
    for n,(x,desired) in enumerate(zip(reference,echo)):
        history=[x]+history[:-1]
        estimate=sum(w*v for w,v in zip(weights,history))>>15
        error=desired-estimate;residual.append(error)
        if n<train_until:
            norm=1+sum(v*v for v in history)
            weights=[w+(step_q15*error*v)//norm for w,v in zip(weights,history)]
        elif frozen is None:frozen=weights[:]
    return dict(residual=residual,weights_q15=weights,frozen_weights_q15=frozen)


def rms(values):
    return math.sqrt(sum(v*v for v in values)/len(values))


def run():
    steady=[0]*80
    data=transmit(steady)
    tone=answer_tone(len(data))
    rng=random.Random(0x2847)
    dibits=[0]*8+[rng.randrange(4) for _ in range(64)]+[0]*8
    samples=transmit(dibits)
    decisions=receive(samples)
    errors=sum(a!=b for a,b in zip(decisions,dibits[1:]))
    reversals=phase_positions([3]*32)
    reference=transmit([rng.randrange(4) for _ in range(256)])
    echo=[round(0.6*(reference[n-3] if n>=3 else 0)+
                0.25*(reference[n-5] if n>=5 else 0)) for n in range(len(reference))]
    cancel=echo_cancel(reference,echo,train_until=1536)
    early=rms(cancel['residual'][64:320]);late=rms(cancel['residual'][1024:1536])
    assert errors==0
    assert spectral_peak(data)['frequency_hz']==CARRIER_HZ
    assert spectral_peak(tone)['frequency_hz']==TONE_HZ
    assert all((b-a)&15==8 for a,b in zip(reversals,reversals[1:]))
    assert late<early/2,(early,late)
    assert cancel['weights_q15']==cancel['frozen_weights_q15']
    return dict(status='reference signatures pass; no DSC2847 execution',
        standard='V.26ter-class diagnostic assumptions',sample_rate=SAMPLE_RATE,
        symbol_rate=SYMBOL_RATE,carrier_hz=CARRIER_HZ,
        phase_steps=list(PHASE_STEPS),
        steady_carrier_peak=spectral_peak(data),answer_tone_peak=spectral_peak(tone),
        reversal_phases=reversals,receive=dict(symbols=len(dibits),errors=errors),
        echo=dict(early_rms=early,late_rms=late,training_samples=1536,
                  frozen_weights_q15=cancel['weights_q15']),
        limitations=['Generated PCM and decisions are a reference model, not microcode or measured board output.',
                     'Receiver assumes known carrier phase/frequency and symbol timing.',
                     'The echo is a two-tap synthetic channel; the LMS is not identified Nokia code.',
                     'Pulse and 8-bit scaling are diagnostic choices, not bit-exact hardware targets.'],
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/reference-modem.json')
    args=parser.parse_args();report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'])


if __name__=='__main__':main()
