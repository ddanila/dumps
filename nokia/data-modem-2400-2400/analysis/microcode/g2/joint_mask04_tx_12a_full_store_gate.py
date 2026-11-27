"""Screen raw-PROM decodes of the direct 12A DAC latch clock."""

import hashlib
import itertools
import json
from functools import reduce
from operator import and_
from pathlib import Path

from joint_mask04_tx_12a_gate import GATE, PROM_DIR

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
PRIOR = RESULTS / 'joint-mask04-tx-12a-gate.json'
OUT = RESULTS / 'joint-mask04-tx-12a-full-store-gate.json'
TARGET = 0x12A
RECEIVE_SPAN = range(0x3E0, 0x400)
THREE = (*GATE, (3, 1, 0))
FOUR = (*THREE, (2, 3, 1))
TI_LS273 = 'https://www.ti.com/lit/ds/symlink/sn74ls273.pdf'


def hits(roms, literals):
    return [pc for pc in range(1024)
            if all(((roms[chip][pc] >> bit) & 1) == value
                   for chip, bit, value in literals)]


def run(out=OUT):
    rom_paths = sorted(PROM_DIR.glob('chip*.bin'))
    roms = [path.read_bytes() for path in rom_paths]
    if len(roms) != 4 or any(len(rom) != 1024 for rom in roms):
        raise ValueError('control PROM fixture changed')
    prior = json.loads(PRIOR.read_text())
    if (prior['fixture']['gate'] != [list(row) for row in GATE] or
            {row['selector']: row['high_sites'] for row in prior['full']}
            != {'40': {'12A': 312054}, '60': {'12A': 312054}}):
        raise ValueError('executed transmitter gate evidence changed')
    target_literals = [(chip, bit, (roms[chip][TARGET] >> bit) & 1)
                       for chip in range(4) for bit in range(8)]
    literal_masks = {literal: sum(1 << pc for pc in range(1024)
                                  if ((roms[literal[0]][pc] >> literal[1]) & 1)
                                  == literal[2])
                     for literal in target_literals}
    isolated = {}
    for width in range(1, 5):
        found = [group for group in itertools.combinations(target_literals, width)
                 if reduce(and_, (literal_masks[literal] for literal in group))
                 == (1 << TARGET)]
        isolated[width] = found
    if (any(isolated[width] for width in (1, 2, 3)) or
            isolated[4] != [
                ((1, 0, 1), (2, 1, 1), (2, 3, 1), (3, 1, 0)),
                ((1, 0, 1), (2, 2, 0), (2, 3, 1), (3, 1, 0)),
            ]):
        raise ValueError('minimum whole-store product changed')
    all_positive = tuple(literal for literal in target_literals
                         if literal[2] == 1)
    positive_hits = hits(roms, all_positive)
    if positive_hits != [0x12A, 0x12F, 0x1DF, 0x29F, 0x3FF]:
        raise ValueError('positive-only alias witness changed')
    old_hits = hits(roms, GATE)
    three_hits = hits(roms, THREE)
    four_hits = hits(roms, FOUR)
    if (len(old_hits), len(three_hits), four_hits) != (111, 15, [TARGET]):
        raise ValueError('direct latch gate decode changed')
    if any(pc in RECEIVE_SPAN for pc in three_hits):
        raise ValueError('three-literal receive-address alias changed')
    if 0x12A not in three_hits or any(0x120 <= pc <= 0x140 and pc != TARGET
                                     for pc in three_hits):
        raise ValueError('three-literal transmit neighborhood changed')
    sources = (Path(__file__), PRIOR, HERE / 'joint_mask04_tx_12a_gate.py',
               *rom_paths)
    report = dict(experiment='full-store raw-PROM decode for direct 12A DAC latch clock',
                  fixture=dict(target_pc=f'{TARGET:03X}',
                               receive_address_span=['3E0', '3FF'],
                               direct_latch='positive-edge 74LS273 capture at 12A-to-127; counter qualification and wiring assumed'),
                  old_two_literal=dict(literals=GATE,
                                       whole_store_hits=len(old_hits),
                                       receive_span_hits=[f'{pc:03X}' for pc in old_hits
                                                          if pc in RECEIVE_SPAN]),
                  three_literal=dict(literals=THREE,
                                     whole_store_hits=[f'{pc:03X}' for pc in three_hits],
                                     receive_span_hits=[],
                                     transmit_neighborhood_hits=['12A']),
                  four_literal=dict(literals=FOUR,
                                    whole_store_hits=['12A'],
                                    minimum_product_width=4,
                                    all_minimum_products=isolated[4]),
                  all_positive_literals=dict(count=len(all_positive),
                                             unavoidable_hits=[f'{pc:03X}'
                                                               for pc in positive_hits]),
                  latch_timing_requirement=dict(datasheet=TI_LS273,
                                                data_setup_ns_min=20,
                                                data_hold_ns_min=5,
                                                inequalities=[
                                                    'settled_12A_Y_valid_time <= 273_clock_time - 20 ns',
                                                    'new_127_Y_change_time >= 273_clock_time + 5 ns'
                                                ]),
                  limitations=[
                      'This is a Boolean decode of the four saved PROMs, not identified PROM-to-gate wiring or a measured 74LS273 clock.',
                      'The 3E0-3FF span is a conservative address screen; no receiver run or clock waveform is needed to prove the three-literal level is low there.',
                      'The datasheet setup/hold minima do not determine the actual PROM, counter, gate, Am2901, wiring or clock-edge propagation ordering.',
                      'The prior two-literal executed transmit trace establishes reached-PC select only for the stated controller fixture.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('three-literal hits', len(result['three_literal']['whole_store_hits']),
          'four-literal', result['four_literal']['whole_store_hits'])
