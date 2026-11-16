#!/usr/bin/env python3
"""Reproduce byte-level inventory without a CPU or hardware model."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import zlib

EXPECTED = '8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a'


def describe(data):
    counts = Counter(data)
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                crc32=f'{zlib.crc32(data):08x}', zero_bytes=counts[0],
                ff_bytes=counts[255], distinct_bytes=len(counts),
                entropy_bits_per_byte=round(-sum((n/len(data))*math.log2(n/len(data))
                                                for n in counts.values()), 6))


def inventory(rom):
    assert len(rom) == 262144, 'Unexpected image length'
    assert hashlib.sha256(rom).hexdigest() == EXPECTED, 'Unexpected ROM revision'
    result = describe(rom)
    last = max(i for i, b in enumerate(rom) if b)
    result.update(last_nonzero_offset=last, zero_tail_start=last+1,
                  zero_tail_bytes=len(rom)-last-1,
                  repeated_whole_image_periods=[n for n in (256,1024,8192,16384,32768,65536,131072)
                                               if rom == rom[:n]*(len(rom)//n)],
                  chunks_32k=[dict(file_offset=i, **describe(rom[i:i+0x8000]))
                              for i in range(0,len(rom),0x8000)])
    result['initial_vector_decoding_8051'] = [
        dict(file_offset=i, opcode='LJMP', target=int.from_bytes(rom[i+1:i+3], 'big'))
        for i in (0,3,0x0b,0x13,0x1b,0x23,0x2b) if rom[i] == 2]
    result['version_string'] = dict(file_offset=0x63e6,
                                   text=rom[0x63e6:rom.index(0,0x63e6)].decode('ascii'))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path(__file__).resolve().parent.parent/'mac304-m27c2001.bin')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    rendered = json.dumps(inventory(args.rom.read_bytes()), indent=2)+'\n'
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end='')
