"""Classify the eight visible DED latch-gap tracks by adjacent DIP pins."""

import hashlib
import json
from pathlib import Path

from photo_ded_latch_bus import PHOTO, THRESHOLDS, components
from PIL import Image

HERE = Path(__file__).resolve().parent
BACK = HERE.parents[2] / 'photos/PXL_20261123_114901193.jpg'
OUT = HERE / 'results/photo-ded-latch-pin-pairing.json'
LS273_RIGHT = {19: '8Q', 18: '8D', 17: '7D', 16: '7Q',
               15: '6Q', 14: '6D', 13: '5D', 12: '5Q'}
LS373_LEFT = {2: '1Q', 3: '1D', 4: '2D', 5: '2Q',
              6: '3Q', 7: '3D', 8: '4D', 9: '4Q'}
TI_LS273 = 'https://www.ti.com/lit/ds/symlink/sn74ls273.pdf'
TI_LS373 = 'https://www.ti.com/lit/ds/symlink/sn74ls373.pdf'


def run(out=OUT):
    image = Image.open(PHOTO).convert('RGB')
    traces = [components(image, threshold) for threshold in THRESHOLDS]
    if any(len(screen) != 8 for screen in traces):
        raise ValueError('visible latch-gap track count changed')
    if any([row['left_y'] for row in screen] != sorted(row['left_y'] for row in screen)
           or [row['right_y'] for row in screen] != sorted(row['right_y'] for row in screen)
           for screen in traces):
        raise ValueError('latch-gap track order changed')
    if any(abs(a['left_y'] - b['left_y']) > 2 or
           abs(a['right_y'] - b['right_y']) > 2
           for a, b in zip(*traces)):
        raise ValueError('thresholds do not agree on track positions')
    pairings = []
    for row, pin273, pin373 in zip(traces[0], LS273_RIGHT, LS373_LEFT):
        signal273 = LS273_RIGHT[pin273]
        signal373 = LS373_LEFT[pin373]
        if signal273[-1] != signal373[-1]:
            raise ValueError('pin-function pairing changed')
        pairings.append(dict(track_left_y=row['left_y'],
                             track_right_y=row['right_y'],
                             ls273_pin=pin273, ls273_signal=signal273,
                             ls373_pin=pin373, ls373_signal=signal373,
                             functional_pair=f'{signal273[-1]}-{signal373[-1]}'))
    if [row['functional_pair'] for row in pairings] != [
            'Q-Q', 'D-D', 'D-D', 'Q-Q', 'Q-Q', 'D-D', 'D-D', 'Q-Q']:
        raise ValueError('photo pin-type sequence changed')
    sources = (Path(__file__), HERE / 'photo_ded_latch_bus.py', PHOTO, BACK)
    report = dict(experiment='photo-inferred pin functions of DED 3558 latch-gap tracks',
                  front_photo=PHOTO.name, back_photo=BACK.name,
                  front_roi_xyxy=(1642, 3230, 1895, 3511),
                  thresholds=THRESHOLDS,
                  pad_assignment='eight ordered front-side tracks appear to meet the eight signal pads on facing chip banks; LS273 right pins 19 through 12 and LS373 left pins 2 through 9, top to bottom',
                  pinout_sources=[TI_LS273, TI_LS373],
                  pairings=pairings,
                  inferred_function_counts=dict(output_to_output=4,
                                                data_to_data=4,
                                                output_to_data=0),
                  limitations=[
                      'Track-to-pad assignment is visual and ordered by proximity; the threshold ROI stops before pad metal and cannot prove continuity beneath the packages.',
                      'The back-side photograph was inspected but not registered to each chip pad; it can contain additional connections.',
                      'Q-Q and D-D pairings, if continuous, disfavor the simple LS373-Q to LS273-D serial hold on these eight visible tracks; they do not identify all board nets or clocks.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print([(row['ls273_pin'], row['ls373_pin'], row['functional_pair'])
           for row in report['pairings']])
