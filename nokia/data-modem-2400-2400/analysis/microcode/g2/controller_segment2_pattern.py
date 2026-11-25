"""Compare executed 8031 port-01 bits with the V.26 ter segment-2 pattern."""

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LONG = HERE / 'results/main-loop-long.json'
ITU = 'https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I%21%21PDF-E&lang=e&type=items'

# Table 3/V.26 ter prints the first 19 phase changes, followed by an ellipsis.
TABLE3 = {
    'GPC': [0, 180, 180, 180, 180, 0, 0, 0, 0, 180, 180, 270,
            90, 180, 0, 0, 90, 180, 0],
    'GPA': [0, 180, 180, 180, 180, 0, 0, 0, 0, 180, 180, 270,
            90, 180, 0, 180, 180, 270, 0],
}
PHASE_TO_BITS = {0: (0, 0), 90: (0, 1), 180: (1, 1), 270: (1, 0)}


def standard_bits(polynomial):
    bits = [bit for phase in TABLE3[polynomial] for bit in PHASE_TO_BITS[phase]]
    delay = 18 if polynomial == 'GPC' else 5
    # Appendix I: Ds[n] = 1 XOR Ds[n-delay] XOR Ds[n-23] for input ones.
    for index in range(23, len(bits)):
        if bits[index] != 1 ^ bits[index - delay] ^ bits[index - 23]:
            raise ValueError(('Table 3 prefix conflicts with Appendix I', polynomial, index))
    for index in range(len(bits), 64):
        bits.append(1 ^ bits[index - delay] ^ bits[index - 23])
    return bits


def serial_bits(values, order):
    return [(value >> bit) & 1 for value in values
            for bit in (range(8) if order == 'lsb_first' else range(7, -1, -1))]


def source_windows(row):
    steps = row['iterations']
    windows = []
    for index, step in enumerate(steps):
        if step['state'] != 'A4' or (index and steps[index - 1]['state'] == 'A4'):
            continue
        block = steps[index:index + 8]
        successor = steps[index + 8] if index + 8 < len(steps) else None
        if (len(block) != 8 or any(item['state'] != 'A4' or
                                   item['line_sources'] != ['FF'] or
                                   len(item['line_bytes']) != 1 for item in block)
                or successor is None or successor['state'] != 'A5' or
                successor['line_sources'] != ['03'] or
                len(successor['line_bytes']) != 1):
            raise ValueError(('A4/A5 source window changed', row['selector'], index))
        values = [int(item['line_bytes'][0], 16) for item in block + [successor]]
        windows.append(dict(first_iteration=index,
                            bytes=[f'{value:02X}' for value in values],
                            first_64_bits_from_second_bit=serial_bits(values, 'lsb_first')[1:65]))
    return windows


def run(out=HERE / 'results/controller-segment2-pattern.json'):
    long = json.loads(LONG.read_text())
    expected = {name: standard_bits(name) for name in TABLE3}
    rows = []
    perfect = []
    for run in long['runs']:
        selector = run['selector']
        values = [int(value, 16) for step in run['iterations']
                  for value in step['line_bytes']]
        if len(values) != run['line_byte_count']:
            raise ValueError(('line byte count changed', selector))
        best_by_polynomial_and_order = []
        for polynomial, target in expected.items():
            for order in ('lsb_first', 'msb_first'):
                bits = serial_bits(values, order)
                scores = [sum(a == b for a, b in zip(bits[start:start + 64], target))
                          for start in range(len(bits) - 63)]
                best = max(scores)
                starts = [index for index, score in enumerate(scores) if score == best]
                best_by_polynomial_and_order.append(dict(polynomial=polynomial,
                                                         bit_order=order,
                                                         matching_bits=best,
                                                         first_start_bit=starts[0],
                                                         equally_best_windows=len(starts)))
                if best == 64:
                    perfect.extend(dict(selector=selector, polynomial=polynomial,
                                        bit_order=order, start_bit=start)
                                   for start in starts)
        windows = source_windows(run) if selector in ('40', '60') else []
        if windows:
            target = expected['GPC' if selector == '40' else 'GPA']
            if len(windows) != 2 or any(window['first_64_bits_from_second_bit'] != target
                                        for window in windows):
                raise ValueError(('A4 segment-2 pattern changed', selector))
            for window in windows:
                del window['first_64_bits_from_second_bit']
        rows.append(dict(selector=selector, port01_bytes=len(values),
                         best_by_polynomial_and_order=best_by_polynomial_and_order,
                         a4_windows=windows))
    expected_perfect = [dict(selector=selector, polynomial=poly,
                             bit_order='lsb_first', start_bit=start)
                        for selector, poly in (('40', 'GPC'), ('60', 'GPA'))
                        for start in (1, 321)]
    if sorted(perfect, key=lambda item: (item['selector'], item['start_bit'])) != expected_perfect:
        raise ValueError(('unexpected exact segment-2 matches', perfect))
    report = dict(
        status='two controller A4 blocks per selector exactly match the 64-bit V.26 ter segment-2 pattern under the executed scrambler choice',
        standard=dict(recommendation='ITU-T V.26 ter (11/1988), Table 1, Table 3 and Appendix I',
                      url=ITU, table3_printed_phase_prefix=TABLE3,
                      extension='After the 19 printed dibits, apply Appendix I self-synchronizing scrambler to input ones, using taps 18/23 for GPC and 5/23 for GPA.',
                      full_64_bits={name: ''.join(map(str, bits)) for name, bits in expected.items()}),
        fixture='Unchanged 8031 ROM, 64 polling iterations per selector, with forced timer expiry, ready status and received selector bytes as in main-loop-long.json',
        rows=rows, exact_64_bit_windows=perfect,
        limitations=['The exact match identifies the controller-generated digital synchronization pattern under this fixture; it does not prove a DAC or analog line waveform.',
                     'The 64-bit match starts at bit 1 of the first A4 byte and takes its final bit from the first A5 byte. Physical symbol timing and the cause of that offset remain unmeasured.',
                     'The first 38 target bits are transcribed from Table 3; the remaining 26 are predicted by the published recurrence, not copied from a full printed table.',
                     'Port-01 routing to the DSC2847 and the natural-duration state schedule remain untraced.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (Path(__file__), LONG,
                                    HERE.parents[1] / 'controller_scrambler.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/controller-segment2-pattern.json')
    args = parser.parse_args()
    report = run(args.out)
    print('exact 64-bit windows', report['exact_64_bit_windows'])
