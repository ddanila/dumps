"""Search other executed ADC visits for the 45/180 preamble distinction."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_protocol_preamble import (
    DATA_SYMBOLS, PREAMBLE_SYMBOLS, VISITS_PER_SYMBOL, candidate, configured,
    execute, fixture, mapped, mapping_with_upper_source, MAPPINGS, receive,
    rotated_transmit)

PRIOR = HERE / 'results/receiver-mask04-preamble-alias.json'
SEED = 0x72A1
ANGLES = (45, 180)
SITES = ('3F8', '3ED_row0', '3ED_row3')
STEADY_SYMBOLS = range(8, 28)


def capture_visits(mapping, base, degrees, middle):
    dibits = [3] * PREAMBLE_SYMBOLS + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost line data')
    samples = [127 - value for value in pcm[:8 * (PREAMBLE_SYMBOLS + DATA_SYMBOLS)]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    adc_visits = len(values)
    cycles = 32 * adc_visits + 47
    scenario = configured(base, values, 'previous', 'overflow', 1)
    captured = {site: [[None] * VISITS_PER_SYMBOL
                       for _ in range(PREAMBLE_SYMBOLS)] for site in SITES}
    adc_event = row_event = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['read_sequence_visits'].get(0x3F8) != adc_visits or
                result['address_counts'].get(0x3ED) != 4 * adc_visits):
            raise ValueError(('receive loop stopped', degrees))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if row['pc'] == 0x3F8:
                symbol, visit = divmod(adc_event, VISITS_PER_SYMBOL)
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != values[adc_event]):
                    raise ValueError('ADC byte mismatch')
                if symbol < PREAMBLE_SYMBOLS:
                    captured['3F8'][symbol][visit] = row['alu']['y']
                adc_event += 1
            if row['pc'] == 0x3ED:
                visit_index, table_row = divmod(row_event, 4)
                symbol, visit = divmod(visit_index, VISITS_PER_SYMBOL)
                if symbol < PREAMBLE_SYMBOLS and table_row in (0, 3):
                    captured[f'3ED_row{table_row}'][symbol][visit] = row['alu']['y']
                row_event += 1
    if (adc_event != adc_visits or row_event != 4 * adc_visits or
            any(None in values for site in SITES
                for values in captured[site])):
        raise ValueError(('capture count or completeness changed', degrees))
    return captured, dict(degrees=degrees, trace_digest=result['trace_digest'],
                          adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                          preamble_capture_sha256={site: hashlib.sha256(
                              bytes(value for symbol in captured[site] for value in symbol)
                          ).hexdigest() for site in SITES})


def run(out=HERE / 'results/receiver-mask04-preamble-visit-screen.json'):
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    prior = {case['degrees']: case for case in json.loads(PRIOR.read_text())['cases']}
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    captures = {}
    cases = []
    for degrees in ANGLES:
        captures[degrees], case = capture_visits(mapping, base, degrees, middle)
        if (case['trace_digest'] != prior[degrees]['trace_digest'] or
                case['adc_stream_sha256'] != prior[degrees]['adc_stream_sha256']):
            raise ValueError(('trace differs from phase-47 alias', degrees))
        cases.append(case)
        print('captured', degrees, flush=True)
    differing_visits = {}
    stable_candidates = []
    for site in SITES:
        first, second = captures[45][site], captures[180][site]
        differing_visits[site] = [visit for visit in range(VISITS_PER_SYMBOL)
                                  if any(first[symbol][visit] != second[symbol][visit]
                                         for symbol in STEADY_SYMBOLS)]
        for visit in differing_visits[site]:
            values45 = {first[symbol][visit] for symbol in STEADY_SYMBOLS}
            values180 = {second[symbol][visit] for symbol in STEADY_SYMBOLS}
            if len(values45) == len(values180) == 1:
                value45, value180 = values45.pop(), values180.pop()
                if value45 != value180:
                    stable_candidates.append(dict(site=site, visit=visit,
                                                  value45=value45, value180=value180,
                                                  distinguishing_bits=[bit for bit in range(8)
                                                                       if (value45 ^ value180) & (1 << bit)]))
    if any(captures[45][site][symbol][47] != captures[180][site][symbol][47]
           for site in SITES for symbol in range(PREAMBLE_SYMBOLS)):
        raise ValueError('prior phase-47 alias changed')
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='all-visit executed preamble screen for 45/180 phase alias',
                  fixture=dict(seed=SEED, angles=ANGLES,
                               sites=SITES, preamble_symbols=PREAMBLE_SYMBOLS,
                               steady_symbols=list(STEADY_SYMBOLS),
                               adc_visits_per_symbol=VISITS_PER_SYMBOL),
                  cases=cases,
                  differing_visits=differing_visits,
                  stable_candidates=stable_candidates,
                  limitations=[
                      'A differing executed byte is only a candidate external capture; no physical latch or USART connection follows from it.',
                      'The stable-symbol criterion covers the tested 45/180 reference preambles, not arbitrary carrier phase, gain or timing.',
                      'The ADC route and four-row dispatch are labelled board hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print({site: len(visits) for site, visits in result['differing_visits'].items()},
          'stable', len(result['stable_candidates']))
