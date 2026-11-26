"""Test a 74LS373 hold stage before a later 74LS273 sample clock."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from joint_mask04_tx_rom_impact import execute_case
from joint_mask04_tx_bank_phase import scenario_for
from joint_mask04_tx_12a_delayed_latch import (
    GATE_REPORT, PRIOR, capturing_execute,
)
from joint_four_row_retention_tx import (
    MAPPINGS, SAMPLE_COUNT, SAMPLE_DIVISOR, TXREADY, candidate, fixture,
    mapped, mapping_with_upper_source,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_joint_tone_training_data import TOTAL_SYMBOLS

HERE = Path(__file__).resolve().parent
PROM_DIR = HERE.parents[2] / 'microcode-810237c-810240c'
EARLIER = HERE / 'results/joint-mask04-tx-12a-delayed-latch.json'
OUT = HERE / 'results/joint-mask04-tx-12a-two-stage-latch.json'
HOLD_GATE = ((1, 0), (2, 1))  # U11.D0 & U17.D1: high at 12A
CLOCK_GATE = ((1, 6), (2, 0), (3, 2))  # U11.D6 & U17.D0 & U18.D2: high at 127


def high(raw, literals):
    return all((raw[chip] >> bit) & 1 for chip, bit in literals)


def gate_screen(mapping, base, roms):
    _, rows = execute_case(mapping, base, 256)
    by_pc = {row['pc']: row['raw'] for row in rows}
    if len(by_pc) != 39:
        raise ValueError('held-tone reached-PC set changed')
    reached = {pc for pc, raw in by_pc.items() if high(raw, CLOCK_GATE)}
    if reached != {0x127}:
        raise ValueError(('candidate 127 gate does not isolate loop entry', reached))
    transitions = Counter((a['pc'], b['pc']) for a, b in zip(rows, rows[1:])
                          if high(a['raw'], CLOCK_GATE) and
                          not high(b['raw'], CLOCK_GATE))
    if transitions != {(0x127, 0x128): 1014}:
        raise ValueError(('candidate 127->128 edge schedule changed', transitions))
    literals = [(chip, bit, polarity) for chip in range(4)
                for bit in range(8) for polarity in (0, 1)]

    def selected(cube):
        return {pc for pc, raw in by_pc.items()
                if all(((raw[chip] >> bit) & 1) == polarity
                       for chip, bit, polarity in cube)}

    if any(selected((literal,)) == {0x127} for literal in literals) or any(
            selected(pair) == {0x127} for pair in itertools.combinations(literals, 2)):
        raise ValueError('unexpected simpler 127-only PROM decode')
    whole_store_hits = [pc for pc in range(1024) if high(
        [rom[pc] for rom in roms], CLOCK_GATE)]
    if len(whole_store_hits) != 7 or 0x127 not in whole_store_hits:
        raise ValueError('candidate gate whole-store census changed')
    return dict(reached_pc_count=len(by_pc), high_only_at='127',
                nand_rising_edges={'127->128': transitions[(0x127, 0x128)]},
                one_or_two_literal_127_decodes=0,
                whole_store_high_addresses=[f'{pc:03X}' for pc in whole_store_hits])


def run(out=OUT):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    roms = [path.read_bytes() for path in sorted(PROM_DIR.glob('chip*.bin'))]
    if len(roms) != 4 or any(len(rom) != 1024 for rom in roms):
        raise ValueError('four control PROM dumps changed')
    screen = gate_screen(mapping, base, roms)
    prior = json.loads(PRIOR.read_text())
    earlier = json.loads(EARLIER.read_text())
    gate = json.loads(GATE_REPORT.read_text())
    controller = json.loads(TXREADY.read_text())
    execute = capturing_execute()
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    cases = []
    for selector in ('40', '60'):
        controller_case = next(x for x in controller['cases'] if x['selector'] == selector)
        old = next(x for x in earlier['cases'] if x['selector'] == selector)
        expected_trace = next(x for x in prior['cases'] if x['selector'] == selector)
        expected_gate = next(x for x in gate['full'] if x['selector'] == selector)
        banks = {}
        for bank in (256, 0):
            result = execute(mapping, scenario_for(base, controller_case, bank),
                             cycles, mode='integrated', trace_limit=0)
            first = result['site_y'][0x12A]
            next_y = result['site_y'][0x127]
            selected = {pc: count for pc, count in result['address_counts'].items()
                        if high([rom[pc] for rom in roms], CLOCK_GATE)}
            if (not result['clean'] or result['completed_cycles'] != cycles or
                    len(first) != len(next_y) or len(first) != 312054 or
                    selected != {0x127: 312054} or
                    result['trace_digest'] != expected_trace['trace_digests'][str(bank)]):
                raise ValueError(('two-stage execution differs', selector, bank))
            if bank == 256 and result['trace_digest'] != expected_gate['trace_digest']:
                raise ValueError('upper-bank PROM gate trace changed')
            # LE373 follows the 12A-only PROM gate. After it closes at
            # 12A->127, Q373 holds the last settled 12A Y through the
            # later counter-qualified CLK273 at 127->128.
            held_then_clocked = [first[SAMPLE_DIVISOR * n]
                                 for n in range(SAMPLE_COUNT)]
            # Control: LE373 stays transparent through the new 127 Y.
            transparent_through_127 = [next_y[SAMPLE_DIVISOR * n + 1]
                                       for n in range(SAMPLE_COUNT)]
            old_phases = {p['timing']: p for p in old['phases']}
            for label, values, timing in (
                    ('held_12a_then_127_clock', held_then_clocked, 'early'),
                    ('transparent_through_127', transparent_through_127, 'late')):
                expected_hash = old_phases[timing]['banks'][str(bank)]['raw_y_sha256']
                if hashlib.sha256(bytes(values)).hexdigest() != expected_hash:
                    raise ValueError(('two-stage byte differs from prior timing',
                                      selector, bank, label))
            banks[str(bank)] = dict(trace_digest=result['trace_digest'],
                                    held_12a_sha256=hashlib.sha256(
                                        bytes(held_then_clocked)).hexdigest(),
                                    through_127_sha256=hashlib.sha256(
                                        bytes(transparent_through_127)).hexdigest(),
                                    held_12a_samples=held_then_clocked,
                                    through_127_samples=transparent_through_127)
        changed_held = sum(a != b for a, b in zip(
            banks['256']['held_12a_samples'], banks['0']['held_12a_samples']))
        changed_through = sum(a != b for a, b in zip(
            banks['256']['through_127_samples'], banks['0']['through_127_samples']))
        if (changed_held != old['phases'][0]['bank_changed_samples'] or
                changed_through != old['phases'][1]['bank_changed_samples']):
            raise ValueError('two-stage bank contrast changed')
        for value in banks.values():
            del value['held_12a_samples']
            del value['through_127_samples']
        cases.append(dict(selector=selector, selected_latch_edges=SAMPLE_COUNT,
                          held_12a_bank_changed_samples=changed_held,
                          transparent_127_bank_changed_samples=changed_through,
                          banks=banks))
        print('two-stage', selector, changed_held, changed_through, flush=True)
    paths = (Path(__file__), EARLIER, PRIOR, GATE_REPORT, TXREADY,
             HERE / 'joint_mask04_tx_rom_impact.py',
             HERE / 'joint_mask04_tx_bank_phase.py',
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *PROM_DIR.glob('chip*.bin'))
    report = dict(experiment='photo-compatible 74LS373 hold then 74LS273 delayed-clock candidate',
                  fixture=dict(le373='U11.D0 & U17.D1 high only at 12A in tested mode',
                               le373_closes='12A->127 after 12A Y settles',
                               clk273='NAND of U11.D6 & U17.D0 & U18.D2 rises at 127->128',
                               clock_divisor=SAMPLE_DIVISOR,
                               selected_samples=SAMPLE_COUNT,
                               trace_cycles=cycles,
                               control='LE373 stays transparent through new 127 Y'),
                  gate_screen=screen, cases=cases,
                  limitations=[
                      'The 74LS373/74LS273 data and clock nets, counter division and relative propagation delays are not traced.',
                      'The 127 decode has seven whole-store hits and is exclusive only in the tested transmit-mode reached-PC set.',
                      'The hold-stage digital bytes are not identified DAC08 input bytes or measured line current.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
