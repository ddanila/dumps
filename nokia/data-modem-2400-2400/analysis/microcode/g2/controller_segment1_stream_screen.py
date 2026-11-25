"""Screen executed controller port-01 streams for direct segment-1 dibits."""

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LONG = HERE / 'results/main-loop-long.json'


def best_run(values):
    best = (0, 0, None)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[end] == values[start]:
            end += 1
        if end - start > best[0]:
            best = (end - start, start, values[start])
        start = end
    return dict(length=best[0], first_symbol=best[1], dibit=best[2])


def cases_for_bytes(values):
    cases = []
    for bit_order in ('lsb_first', 'msb_first'):
        bits = [(byte >> bit) & 1 for byte in values
                for bit in (range(8) if bit_order == 'lsb_first'
                            else range(7, -1, -1))]
        for symbol_offset in (0, 1):
            dibits = [bits[index] | (bits[index + 1] << 1)
                      for index in range(symbol_offset, len(bits) - 1, 2)]
            cases.append(dict(bit_order=bit_order, symbol_offset_bits=symbol_offset,
                              symbols=len(dibits), longest_identical=best_run(dibits)))
    return cases


def run(out=HERE / 'results/controller-segment1-stream-screen.json'):
    source = json.loads(LONG.read_text())
    results = []
    for run in source['runs']:
        values = [int(value, 16) for row in run['iterations']
                  for value in row['line_bytes']]
        if len(values) != run['line_byte_count']:
            raise ValueError('long-run byte count changed')
        cases = cases_for_bytes(values)
        if max(case['longest_identical']['length'] for case in cases) >= 32:
            raise ValueError('a direct 32-dibit segment-1 candidate appeared')
        results.append(dict(selector=run['selector'], line_bytes=len(values),
                            cases=cases))
    if len(results) != 4 or {row['selector'] for row in results} != {'00', '20', '40', '60'}:
        raise ValueError('long-run controller classes changed')
    report = dict(
        status='direct two-bit grouping of recorded scrambled port-01 bytes cannot supply segment 1 in this fixture',
        target='32 consecutive identical 180-degree dibits; any fixed invert/swap of the two bit lanes preserves equal-dibit run length',
        fixture=dict(controller='unchanged ROM 64-iteration forced-timer polling-loop run',
                     bit_orders=['lsb_first', 'msb_first'],
                     symbol_bit_offsets=[0, 1],
                     byte_stream='all recorded port-01 writes, including state boundaries'),
        results=results,
        limitations=['The 8031 timer expiry, serial ready/receive events and selector are diagnostic fixtures.',
                     'This excludes only direct contiguous two-bit grouping of the recorded port-01 bytes with fixed lane permutation/inversion; a descrambler, autonomous DSP pattern, or different data path is not screened.',
                     'No physical route from port 01 to the DSC2847 or line output is established.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (Path(__file__), LONG)})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/controller-segment1-stream-screen.json')
    args = parser.parse_args()
    report = run(args.out)
    for row in report['results']:
        print(row['selector'], row['line_bytes'],
              [case['longest_identical']['length'] for case in row['cases']])
