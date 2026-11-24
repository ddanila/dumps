"""Independent ROM signatures for G2; this does not execute Nokia microcode."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
SHA = '312fa21f50203c7b84ec0a4b4aea62ca343b2a579c38687111342368b1f04d58'
STANDARD = 'https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I!!PDF-E&lang=e&type=items'
# Table 1, indexed by first-bit * 2 + second-bit, first bit transmitted first.
DEGREES = [0, 90, 270, 180]


def occurrences(data, pattern):
    return [i for i in range(len(data)-len(pattern)+1)
            if list(data[i:i+len(pattern)]) == list(pattern)]


def signed(value):
    return value if value < 128 else value-256


def phase_sequence(dibits, increments, initial=0):
    phase = initial
    result = []
    for dibit in dibits:
        if type(dibit) is not int or not 0 <= dibit < 4:
            raise ValueError('dibit must be 0..3 in first-bit-first order')
        phase = (phase + increments[dibit]) % 16
        result.append(phase)
    return result


def inspect(data):
    if len(data) != 512 or hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError('unexpected lookup PROM')
    # Express quarter turns exactly in the 16-entry phase representation.
    increments = [degree//90*4 for degree in DEGREES]
    coarse = [signed(v) for v in data[:16]]
    sine = [round(127*math.sin(2*math.pi*i/16)) for i in range(16)]
    fine = list(data[0x100:0x141])
    expected_fine = [round(127*math.sin(math.pi*i/128)) for i in range(65)]
    match = occurrences(data, increments)
    # Test the exact stored bytes, not a regenerated Gray map.
    stored = list(data[0x7c:0x80])
    dibits = [0, 1, 2, 3, 3, 2, 1, 0]
    phases = phase_sequence(dibits, stored)
    reversals = phase_sequence([3]*32, stored)
    return dict(
        status='reference signature; no microcode execution or physical routing inferred',
        rom_sha256=SHA, standard=dict(url=STANDARD, section='2.5.2.1, Table 1',
            dibit_order=['00','01','10','11'], degrees=DEGREES),
        gray16=dict(expected=increments, exact_occurrences=[f'{i:03X}' for i in match],
            stored_07c=stored, compared_068=list(data[0x68:0x6c]),
            compared_06c=list(data[0x6c:0x70]),
            candidate_068_matches=list(data[0x68:0x6c])==[d//90 for d in DEGREES],
            candidate_06c_matches=list(data[0x6c:0x70])==[d//90 for d in DEGREES]),
        sine16=dict(actual=coarse, expected=sine, exact=coarse==sine,
            wrap_010_014=list(data[0x10:0x15]),wrap_exact=data[0x10:0x15]==data[:5]),
        sine256_quarter=dict(exact=fine==expected_fine,
            mismatches=[dict(address=f'{0x100+i:03X}',actual=a,expected=b)
                        for i,(a,b) in enumerate(zip(fine,expected_fine)) if a!=b]),
        reference_only=dict(dibits=dibits,phases=phases,
            samples_at_symbol_phase=[coarse[p] for p in phases],
            segment1_dibits=[3]*32,segment1_phases=reversals,
            hypothetical_sample_rate=9600,carrier_phase_step=3,
            carrier_frequency=9600*3/16,
            carrier_one_period=[coarse[(3*n)%16] for n in range(16)]),
        limitations=[
            'Four-byte match is a candidate address, not a unique identification of the standard.',
            'No tested microcode trace yet derives these addresses from the real USART bitstream.',
            'The 9600 Hz sample rate is hypothetical; this calculation is not a DAC waveform.',
            'Coefficient fitting for 141-1CF and controller A1/A2 remain outstanding.',
            'No G2 transmit, receive, or echo-cancellation acceptance criterion passes here.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/table-signatures.json')
    args=parser.parse_args()
    report=inspect(ROM.read_bytes())
    report['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('gray16','sine256_quarter')},indent=2))


if __name__=='__main__':
    main()
