"""Check a raw-PROM gate that can capture settled PC12A Y."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from joint_mask04_tx_rom_impact import execute_case
from joint_mask04_tx_bank_phase import (EXECUTE, scenario_for)
from joint_four_row_retention_tx import (MAPPINGS, candidate, fixture, mapped,
                                         mapping_with_upper_source, TXREADY)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_joint_tone_training_data import TOTAL_SYMBOLS

HERE = Path(__file__).resolve().parent
PROM_DIR = HERE.parents[2] / 'microcode-810237c-810240c'
GATE = ((1, 0, 1), (2, 1, 1))  # U11.D0 & U17.D1


def level(raw, literals=GATE):
    return all(((raw[chip] >> bit) & 1) == value
               for chip, bit, value in literals)


def gate_sites(rows):
    high, falls, captured = Counter(), Counter(), []
    for row in rows:
        if level(row['raw']):
            high[row['pc']] += 1
    for before, after in zip(rows, rows[1:]):
        if level(before['raw']) and not level(after['raw']):
            falls[(before['pc'], after['pc'])] += 1
            captured.append(before['alu']['y'])
    return high, falls, captured


def short_screen(mapping, base):
    upper, a = execute_case(mapping, base, 256)
    lower, b = execute_case(mapping, base, 0)
    if [row['pc'] for row in a] != [row['pc'] for row in b]:
        raise ValueError('bank intervention changed control path')
    observations = {}
    for bank, result, rows in ((256, upper, a), (0, lower, b)):
        high, falls, captured = gate_sites(rows)
        if (high != {0x12A: 1014} or
                falls != {(0x12A, 0x127): 1013} or
                len(captured) != 1013):
            raise ValueError(('candidate 12A clock changed', bank, high, falls))
        observations[bank] = dict(trace_digest=result['trace_digest'],
                                  captured=captured)
    masks = Counter(x ^ y for x, y in zip(observations[256]['captured'],
                                         observations[0]['captured']) if x != y)
    if masks != {1: 221}:
        raise ValueError(('bank contrast changed', masks))
    raw_by_pc = {row['pc']: row['raw'] for row in a}
    literals = [(chip, bit, value) for chip in range(4)
                for bit in range(8) for value in (0, 1)]
    single = [literal for literal in literals if
              {pc for pc, raw in raw_by_pc.items() if level(raw, (literal,))}
              == {0x12A}]
    pairs = [pair for pair in itertools.combinations(literals, 2) if
             pair[0][:2] != pair[1][:2] and
             {pc for pc, raw in raw_by_pc.items() if level(raw, pair)}
             == {0x12A}]
    if single or pairs != [GATE]:
        raise ValueError(('minimal gate changed', single, pairs))
    return dict(reached_pc_count=len(raw_by_pc),
                unique_one_literal_gates=len(single),
                unique_two_literal_gates=[pairs[0]],
                high_sites={'12A': 1014},
                nand_rising_edges={'12A->127': 1013},
                bank_xor_masks={f'{mask:02X}': n for mask, n in masks.items()},
                trace_digests={str(bank): observations[bank]['trace_digest']
                               for bank in (256, 0)})


def full_screen(mapping, base):
    # The PROM decode is a pure function of the instruction address. Check
    # every address reached with the actual controller traffic without storing
    # million-word traces.
    from execute import execute
    controller = json.loads(TXREADY.read_text())
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    roms = [path.read_bytes() for path in sorted(PROM_DIR.glob('chip*.bin'))]
    if len(roms) != 4 or any(len(rom) != 1024 for rom in roms):
        raise ValueError('control PROM fixture changed')
    cases = []
    for selector in ('40', '60'):
        controller_case = next(row for row in controller['cases']
                               if row['selector'] == selector)
        scenario = scenario_for(base, controller_case, 256)
        result = execute(mapping, scenario, cycles, mode='integrated',
                         trace_limit=0)
        counts = result['address_counts']
        high = {pc: count for pc, count in counts.items()
                if level([roms[chip][pc] for chip in range(4)])}
        if (not result['clean'] or result['completed_cycles'] != cycles or
                high != {0x12A: 312054}):
            raise ValueError(('full-stream gate select changed', selector, high))
        cases.append(dict(selector=selector,
                          reached_pc_count=len(counts),
                          high_sites={'12A': high[0x12A]},
                          trace_digest=result['trace_digest']))
    return cases


def run(out=HERE / 'results/joint-mask04-tx-12a-gate.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    short = short_screen(mapping, base)
    full = full_screen(mapping, base)
    previous = json.loads((HERE / 'results/joint-mask04-tx-bank-phase.json').read_text())
    for row in full:
        prior = next(case for case in previous['cases']
                     if case['selector'] == row['selector'])
        if row['trace_digest'] != prior['trace_digests']['256']:
            raise ValueError('full-stream bank-phase replay did not match')
    roms = [path.read_bytes() for path in sorted(PROM_DIR.glob('chip*.bin'))]
    store_hits = [pc for pc in range(1024)
                  if level([roms[chip][pc] for chip in range(4)])]
    if 0x12A not in store_hits or len(store_hits) <= 1:
        raise ValueError('whole-store gate census changed')
    paths = (Path(__file__), EXECUTE,
             HERE / 'joint_mask04_tx_rom_impact.py',
             HERE / 'joint_mask04_tx_bank_phase.py',
             TXREADY,
             HERE / 'results/joint-mask04-tx-bank-phase.json',
             MAPPINGS['q3'], *PROM_DIR.glob('chip*.bin'))
    report = dict(experiment='PROM-decodable settled-12A DAC latch candidate',
                  fixture=dict(gate=GATE, bank_upper=256, bank_lower=0,
                               short_cycles=4096,
                               full_cycles=(TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4,
                               latch_edge='NAND rising as 12A PROM level falls at 127 fetch'),
                  short=short, full=full,
                  whole_store_gate_hits=len(store_hits),
                  limitations=[
                      'The candidate gate is unique only among reached PCs in the tested transmit mode; it is high at other words elsewhere in the 1024-word store.',
                      'PROM-to-gate wiring, gate-to-counter/LS273 clock, and setup/hold timing are assumptions.',
                      'The observed 12A Y bank dependence would reach a DAC only under a compatible Y-bus and latch-data route.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
