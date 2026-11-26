"""Check whether captured 3F9/3FA bytes carry more than ADC high nibbles."""

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from receiver_mask04_carrier_phase_screen import rotated_transmit

HERE = Path(__file__).resolve().parent
CODEBOOK = HERE / 'results/joint-mask04-receive-3f9-3fa-codebook.json'
AUDIT = HERE / 'results/joint-mask04-12a-3f9-key-audit.json'
FULL = HERE / 'results/receiver-mask04-3f9-fullbyte-screen.json'


def samples(case):
    rng = random.Random(case['seed'])
    middle = [rng.randrange(4) for _ in range(16)]
    pcm = rotated_transmit([0] * 8 + middle + [0] * 8,
                           case['degrees'])
    scaled = [max(-127, min(127, round(v * case['gain']))) for v in pcm]
    selected = [127 - v for v in scaled[
        SAMPLE_START + case['offset']:
        SAMPLE_START + case['offset'] + LONG_SAMPLES]]
    if len(selected) != LONG_SAMPLES:
        raise ValueError('independent ADC sample window changed')
    held = [value for index, value in enumerate(selected)
            for _ in range(47 if index % 8 < 7 else 46)]
    if ('adc_sha256' in case and
            hashlib.sha256(bytes(held)).hexdigest() != case['adc_sha256']):
        raise ValueError('saved independent ADC hash changed')
    return selected


def check_rows(rows, sample_windows, books):
    counts = Counter()
    bad = []
    observed = {'3F9': {}, '3FA': {}}
    for row, adc_octet in zip(rows, sample_windows):
        for j in range(2):
            nibble = adc_octet[j] >> 4
            counts[nibble] += 1
            for site, field in (('3F9', 'y3f9_at_phases'),
                                ('3FA', 'y3fa_at_phases')):
                value = row[field][j]
                allowed = books[site]['values_by_current'][f'{nibble:X}']
                if f'{value:02X}' not in allowed:
                    bad.append(dict(site=site, nibble=nibble, y=value,
                                    symbol=row.get('symbol'), phase=j))
                observed[site].setdefault(f'{nibble:X}', set()).add(value)
    return counts, bad, observed


def run(out=HERE / 'results/receiver-mask04-3f9-adc-equivalence.json'):
    codebook = json.loads(CODEBOOK.read_text())
    audit = json.loads(AUDIT.read_text())
    full = json.loads(FULL.read_text())
    books = codebook['codebooks']
    cases = []
    totals = Counter()
    observed = {'3F9': {}, '3FA': {}}
    for case in full['training'] + full['holdout']:
        adc = samples(case)
        windows = [adc[symbol * 8:symbol * 8 + 8]
                   for symbol in range(2, 14)]
        if case['seed'] == full['training'][0]['seed'] and case['gain'] == 1.0:
            earlier = next(c for c in audit['independent']
                           if c['degrees'] == case['degrees'])
            if (case['trace_digest'] != earlier['trace_digest'] or
                    windows != [row['adc_octet'] for row in earlier['rows']]):
                raise ValueError('saved nominal independent rows changed')
        counts, bad, local = check_rows(case['rows'], windows, books)
        if bad:
            raise ValueError(('independent 3F9/3FA codebook mismatch', bad[:4]))
        totals.update(counts)
        for site in observed:
            for nibble, values in local[site].items():
                observed[site].setdefault(nibble, set()).update(values)
        cases.append(dict(kind='independent', seed=case['seed'],
                          degrees=case['degrees'], gain=case['gain'],
                          offset=case['offset'], trace_digest=case['trace_digest'],
                          checked_phase_samples=sum(counts.values()),
                          y_mismatches=0))
    for case in audit['loopbacks']:
        windows = [row['adc_octet'] for row in case['rows']]
        counts, bad, local = check_rows(case['rows'], windows, books)
        if bad:
            raise ValueError(('buffered 3F9/3FA codebook mismatch', bad[:4]))
        totals.update(counts)
        for site in observed:
            for nibble, values in local[site].items():
                observed[site].setdefault(nibble, set()).update(values)
        cases.append(dict(kind='buffered', selector=case['selector'],
                          trace_digest=case['rx_trace_digest'],
                          checked_phase_samples=sum(counts.values()),
                          y_mismatches=0))
    if sum(totals.values()) != 320:
        raise ValueError('sample count changed')
    aliases = []
    for a in range(16):
        for b in range(a + 1, 16):
            if all(books[site]['values_by_current'][f'{a:X}'] ==
                   books[site]['values_by_current'][f'{b:X}']
                   for site in ('3F9', '3FA')):
                aliases.append([f'{a:X}', f'{b:X}'])
    if aliases != [['9', 'D']]:
        raise ValueError('codebook alias set changed')
    report = dict(experiment='executed 3F9/3FA fixed-phase output versus current ADC high nibble',
                  fixture=dict(phases=[46, 93], sites=['3F9', '3FA'],
                               codebook='prior three legal carrier phases; no refit'),
                  cases=cases, checked_phase_samples=sum(totals.values()),
                  checked_y_bytes=2 * sum(totals.values()),
                  adc_high_nibble_counts={f'{n:X}': totals[n] for n in range(16)},
                  distinct_high_nibbles=sum(totals[n] > 0 for n in range(16)),
                  indistinguishable_adc_high_nibble_pairs=aliases,
                  observed_y_by_adc_high_nibble={
                      site: {nibble: [f'{v:02X}' for v in sorted(values)]
                             for nibble, values in sorted(group.items())}
                      for site, group in observed.items()},
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), CODEBOOK, AUDIT, FULL)},
                  limitations=[
                      'The check covers only the two frozen capture visits per symbol, not every executed visit.',
                      'The ADC pin mapping, symbol clock and analog line remain modeled assumptions.',
                      'Functional equivalence at these sites does not identify the physical receiver output circuit.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('checked', result['checked_phase_samples'], 'samples and',
          result['checked_y_bytes'], 'Y bytes across', len(result['cases']),
          'executed traces')
