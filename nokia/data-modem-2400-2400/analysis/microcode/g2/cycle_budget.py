"""Compare the observed q3 DAC-loop period with explicit oscillator/divider cases."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ASSUMED=HERE.parent/'assumed'
OSCILLATOR_HZ=14_400_000
SAMPLE_HZ=9_600
BAUD=1_200


def build():
    source=ASSUMED/'results/frame-dac-bridge/report.json'
    bridge=json.loads(source.read_text())
    complete=[r for r in bridge['runs'] if r['microcode_started']]
    assert len(complete)==6
    periods=set()
    for r in complete:
        cycles=r['finding']['update_cycles']
        assert cycles==list(range(55,256,12))
        assert r['finding']['classification']['outcome']=='repeat'
        periods.update(b-a for a,b in zip(cycles,cycles[1:]))
        trace=ASSUMED/'results/frame-dac-bridge'/r['microcode_path']/'trace.jsonl'
        pcs=[json.loads(line) for line in trace.read_text().splitlines()]
        observed=[row['cycle'] for row in pcs if row['pc']==0x392]
        assert observed==cycles
    assert periods=={12}
    candidates=[]
    for divisor in range(1,5):
        microclock=Fraction(OSCILLATOR_HZ,divisor)
        sample_budget=microclock/SAMPLE_HZ
        baud_budget=microclock/BAUD
        transfer_rate=microclock/12
        candidates.append(dict(divisor=divisor,microclock_hz=int(microclock),
            microinstructions_per_9600_sample=int(sample_budget),
            microinstructions_per_1200_baud=int(baud_budget),
            unpaced_transfer_rate_hz=int(transfer_rate),
            transfer_rate_over_9600=[(transfer_rate/SAMPLE_HZ).numerator,
                                      (transfer_rate/SAMPLE_HZ).denominator]))
    return dict(status='conditional timing comparison; no clock divider or DAC wiring recovered',
        oscillator_hz=OSCILLATOR_HZ,assumed_sample_hz=SAMPLE_HZ,
        assumed_baud=BAUD,observed_q3_dac_loop_period_microinstructions=12,
        compared_complete_bridge_transactions=len(complete),candidates=candidates,
        divider_if_every_12_cycle_transfer_were_9600_hz=125,
        interpretation='For k=1..4 the modeled 12-cycle transfer repeats 31.25 to 125 times faster than 9600 Hz. A slower divider or output gating is required for one transfer per sample.',
        limitations=['The 14.4 MHz marking does not establish the 8X02 microclock divider.',
            'The DAC connection and per-load transfer strobes are declared G1 hypotheses.',
            'The 9600 Hz rate is a candidate 8-sample-per-baud model, not a measured sample rate.',
            'This does not exclude a transmitter elsewhere in the microcode.'],
        source_sha256={str(p.relative_to(HERE.parent.parent.parent.parent.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),source,ASSUMED/'frame_dac_bridge.py',ASSUMED/'frame-dac-bridge.json')})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/cycle-budget.json')
    args=parser.parse_args();report=build();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print([(r['divisor'],r['microinstructions_per_9600_sample'],
        r['unpaced_transfer_rate_hz']) for r in report['candidates']])

if __name__=='__main__':main()
