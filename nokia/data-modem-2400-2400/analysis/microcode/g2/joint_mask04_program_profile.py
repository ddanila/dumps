"""Materialize the fixed G2 joint map for the evidence-linked program listing."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent / 'assumed'), str(HERE)]

from common import decode, read, save
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

OUT = HERE.parent / 'assumed/results/program-reading/joint-mask04-mapping.json'


def run(out=OUT):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    rows = decode(mapping)
    sequencer = decode(read(HERE.parent / 'assumed/sequencer.json'))
    fields = ('raw', 'command', 'branch', 'select', 'direct')
    if any(any(row[field] != reference[field] for field in fields)
           for row, reference in zip(rows, sequencer)):
        raise ValueError('joint map changes shared control-flow decode')
    save(out, mapping)
    return hashlib.sha256(out.read_bytes()).hexdigest()


if __name__ == '__main__':
    print(run())
