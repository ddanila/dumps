"""Count visible front-side tracks between DED 3558 latch pad banks."""

import hashlib
import json
from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'
OUT = HERE / 'results/photo-ded-latch-bus.json'
# Original-image pixels between the right pads of the 74LS273 and left pads
# of the adjacent 74LS373. The pad/lead contact regions themselves are cut out.
ROI = (1642, 3230, 1895, 3511)
THRESHOLDS = ((105, 125, 65), (100, 120, 60))


def components(image, threshold):
    x0, y0, x1, y1 = ROI
    width, height = x1 - x0, y1 - y0
    gmin, bmin, green_minus_red = threshold
    pixels = image.load()
    mask = bytearray(width * height)
    for y in range(y0, y1):
        for x in range(x0, x1):
            red, green, blue = pixels[x, y]
            if (green > gmin and blue > bmin and
                    green - red > green_minus_red and
                    8 < blue - green < 55):
                mask[(y - y0) * width + x - x0] = 1
    seen = bytearray(len(mask))
    tracks = []
    for start, enabled in enumerate(mask):
        if not enabled or seen[start]:
            continue
        queue = deque([start])
        seen[start] = 1
        points = []
        while queue:
            item = queue.popleft()
            row, column = divmod(item, width)
            points.append((column + x0, row + y0))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if not (dx or dy):
                        continue
                    nx, ny = column + dx, row + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        neighbor = ny * width + nx
                        if mask[neighbor] and not seen[neighbor]:
                            seen[neighbor] = 1
                            queue.append(neighbor)
        left = [y for x, y in points if x0 <= x < x0 + 20]
        right = [y for x, y in points if x1 - 20 <= x < x1]
        if len(points) <= 100 or not left or not right:
            continue
        tracks.append(dict(left_y=round(sum(left) / len(left)),
                           right_y=round(sum(right) / len(right)),
                           pixels=len(points),
                           bounds=[min(x for x, _ in points),
                                   min(y for _, y in points),
                                   max(x for x, _ in points),
                                   max(y for _, y in points)]))
    return sorted(tracks, key=lambda row: row['left_y'])


def run(out=OUT):
    photo_bytes = PHOTO.read_bytes()
    image = Image.open(PHOTO).convert('RGB')
    if image.size != (3072, 4080):
        raise ValueError('front-photo dimensions changed')
    screens = [components(image, threshold) for threshold in THRESHOLDS]
    if (any(len(screen) != 8 for screen in screens) or
            any(abs(a['left_y'] - b['left_y']) > 2 or
                abs(a['right_y'] - b['right_y']) > 2
                for a, b in zip(*screens))):
        raise ValueError('eight-track photo count is not threshold-stable')
    report = dict(experiment='visible DED 3558 front-side latch-pad track bundle',
                  photo_sha256=hashlib.sha256(photo_bytes).hexdigest(),
                  image_size=image.size, roi_xyxy=ROI,
                  threshold_screens=[dict(green_min=t[0], blue_min=t[1],
                                          green_minus_red_min=t[2], tracks=screen)
                                     for t, screen in zip(THRESHOLDS, screens)],
                  interpretation='eight visible components cross the gap between the 74LS273 right-pad bank and the 74LS373 left-pad bank',
                  limitations=[
                      'The pixel components stop before package pads and do not prove electrical continuity or pin numbers.',
                      'The photograph does not identify signal direction, output enables, latch clocks or a serial 74LS373-to-74LS273 data route.',
                      'Back-side traces and hidden copper may connect the devices differently.'
                  ],
                  source_sha256={str(Path(__file__).relative_to(HERE.parents[4])):
                                 hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('stable visible gap tracks', len(screens[0]),
          [(row['left_y'], row['right_y']) for row in screens[0]])
    return report


if __name__ == '__main__':
    run()
