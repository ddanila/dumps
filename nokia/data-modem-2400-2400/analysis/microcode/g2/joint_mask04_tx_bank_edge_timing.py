"""Compare pre-edge and settled Y data at the raw U10.D2 transmit edges."""

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from joint_mask04_tx_rom_impact import execute_case
from joint_four_row_retention_tx import (MAPPINGS, candidate, fixture, mapped,
                                         mapping_with_upper_source)

FULL = HERE / 'results/joint-mask04-tx-bank-phase.json'


def run(out=HERE / 'results/joint-mask04-tx-bank-edge-timing.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    upper, upper_rows = execute_case(mapping, base, 256)
    lower, lower_rows = execute_case(mapping, base, 0)
    sites = {
        'rising_at_129': (0x128, 0x129, 0, 1),
        'falling_at_12a': (0x129, 0x12A, 1, 0),
    }
    counts = {name: dict(edges=0, pre_y_differences=0,
                         settled_y_differences=0,
                         pre_y_xor_masks=Counter(),
                         settled_y_xor_masks=Counter())
              for name in sites}
    for index in range(1, len(upper_rows)):
        a_before, a_after = upper_rows[index - 1], upper_rows[index]
        b_before, b_after = lower_rows[index - 1], lower_rows[index]
        if (a_before['pc'] != b_before['pc'] or
                a_after['pc'] != b_after['pc']):
            raise ValueError(('bank switch changed path', index))
        if a_after['cycle'] < 40:
            continue
        for name, (previous_pc, pc, old_level, new_level) in sites.items():
            if (a_before['pc'], a_after['pc']) != (previous_pc, pc):
                continue
            for before, after in ((a_before, a_after), (b_before, b_after)):
                if (((before['raw'][0] >> 2) & 1) != old_level or
                        ((after['raw'][0] >> 2) & 1) != new_level):
                    raise ValueError(('U10.D2 edge changed', name, index))
            row = counts[name]
            row['edges'] += 1
            pre_mask = a_before['alu']['y'] ^ b_before['alu']['y']
            settled_mask = a_after['alu']['y'] ^ b_after['alu']['y']
            row['pre_y_differences'] += pre_mask != 0
            row['settled_y_differences'] += settled_mask != 0
            if pre_mask:
                row['pre_y_xor_masks'][pre_mask] += 1
            if settled_mask:
                row['settled_y_xor_masks'][settled_mask] += 1
    if any(row['edges'] != 1014 for row in counts.values()):
        raise ValueError(('edge count changed', counts))
    full = json.loads(FULL.read_text())
    for case in full['cases']:
        if next(site for site in case['sites'] if site['pc'] == '12A')['phases_with_changed_samples'] != 375:
            raise ValueError('full-stream 12A phase result changed')
    report = dict(experiment='selected-ROM-bank dependence at raw U10.D2 latch edges',
                  fixture=dict(cycles=4096,
                               d127='88 held tone input',
                               upper_bank=256, lower_bank=0,
                               mapping='joint lower mask 04 / q3 transmitter',
                               raw_bit='U10.D2',
                               comparison='Y before an edge versus Y after the new instruction settles'),
                  traces=dict(upper=upper['trace_digest'],
                              lower=lower['trace_digest']),
                  edges={name: {key: (dict(sorted((f'{mask:02X}', amount)
                                                      for mask, amount in value.items()))
                                      if isinstance(value, Counter) else value)
                                for key, value in row.items()}
                         for name, row in counts.items()},
                  full_stream_phase_result=dict(
                      selectors=[case['selector'] for case in full['cases']],
                      post_12a_phases_with_changed_samples=
                          {case['selector']: next(site for site in case['sites']
                                                  if site['pc'] == '12A')['phases_with_changed_samples']
                           for case in full['cases']}),
                  limitations=[
                      'The photos do not establish U10.D2-to-LS273 CLK, inversion, divider or Y-bus wiring.',
                      'Pre-edge and settled-data capture are timing hypotheses; this does not resolve propagation delays or setup/hold on the physical board.',
                      'The 4,096-cycle edge result is a held-tone fixture; the linked full-stream result covers controller call and answer data.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
