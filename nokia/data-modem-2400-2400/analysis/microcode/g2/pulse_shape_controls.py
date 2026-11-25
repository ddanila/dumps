"""Compare broad pulse fits with a periodic control on ROM 16F-1CF."""

import hashlib
import json
import math
from pathlib import Path

from pulse_fit import ROM, fit, raised_cosine, root_raised_cosine

HERE = Path(__file__).resolve().parent
START, END = 0x16F, 0x1D0


def solve3(matrix, vector):
    rows = [list(row) + [value] for row, value in zip(matrix, vector)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        if abs(scale) < 1e-12:
            return None
        rows[col] = [value / scale for value in rows[col]]
        for row in range(3):
            if row != col:
                multiple = rows[row][col]
                rows[row] = [a - multiple*b for a, b in zip(rows[row], rows[col])]
    return [row[-1] for row in rows]


def sine_fit(values, period):
    basis = [(math.sin(2*math.pi*i/period),
              math.cos(2*math.pi*i/period), 1.0)
             for i in range(len(values))]
    gram = [[sum(row[j]*row[k] for row in basis) for k in range(3)]
            for j in range(3)]
    vector = [sum(row[j]*value for row, value in zip(basis, values))
              for j in range(3)]
    coefficients = solve3(gram, vector)
    if coefficients is None:
        return None
    prediction = [sum(a*b for a, b in zip(coefficients, row)) for row in basis]
    mse = sum((a-b)**2 for a, b in zip(values, prediction)) / len(values)
    return mse, coefficients, prediction


def run(out=HERE / 'results/pulse-shape-controls.json'):
    image = ROM.read_bytes()
    values = [byte if byte < 128 else byte-256 for byte in image[START:END]]
    mean = sum(values) / len(values)
    variance = sum((value-mean)**2 for value in values) / len(values)
    pulse_results = []
    for name, function in (('raised_cosine', raised_cosine),
                           ('root_raised_cosine', root_raised_cosine)):
        for samples in (16, 24, 32, 40, 48, 64):
            best = None
            for beta_tenths in range(1, 11):
                beta = beta_tenths / 10
                for center_halves in range(2*len(values)):
                    center = center_halves / 2
                    template = [function((i-center)/samples, beta)
                                for i in range(len(values))]
                    fitted = fit(values, template)
                    if fitted is None:
                        continue
                    mse, scale, offset = fitted
                    if best is None or mse < best['mse']:
                        predictions = [scale*x+offset for x in template]
                        best = dict(mse=mse, samples_per_symbol=samples,
                                    rolloff=beta, center_index=center,
                                    scale=scale, offset=offset,
                                    rounded_exact=sum(round(a) == b for a, b
                                                      in zip(predictions, values)))
            pulse_results.append(dict(family=name, **best,
                                      r_squared=1-best['mse']/variance))
    sine = None
    for period_quarters in range(160, 1361):  # 40..340 in quarter-byte steps.
        period = period_quarters / 4
        fitted = sine_fit(values, period)
        if fitted is None:
            continue
        mse, coefficients, prediction = fitted
        if sine is None or mse < sine['mse']:
            sine = dict(period_bytes=period, coefficients=coefficients,
                        mse=mse, r_squared=1-mse/variance,
                        rounded_exact=sum(round(a) == b for a, b
                                          in zip(prediction, values)))
    paths = [Path(__file__), HERE/'pulse_fit.py', ROM]
    report = dict(status='exploratory shape control, no DSP role identified',
                  window=f'{START:03X}-{END-1:03X}', count=len(values),
                  signed_values=values, variance=variance,
                  search=dict(pulse_samples_per_symbol=[16,24,32,40,48,64],
                              pulse_rolloff_step=0.1, pulse_center_step=0.5,
                              sine_period_range=[40,340], sine_period_step=0.25,
                              all_families='free scale and offset; sine has free phase'),
                  pulse_fits=pulse_results, sine_control=sine,
                  limitations=[
                      'The wider pulse rates were explored after inspecting this ROM window; no claim of physical sample rate follows.',
                      'Both pulse and sine fits use free shape/phase and amplitude parameters; high R squared alone does not identify a table role.',
                      'The physical table boundaries, address order and microcode consumer are not established.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    best = max(report['pulse_fits'], key=lambda row: row['r_squared'])
    print('best pulse', best['family'], best['samples_per_symbol'],
          round(best['r_squared'], 4))
    print('sine', report['sine_control']['period_bytes'],
          round(report['sine_control']['r_squared'], 4))
