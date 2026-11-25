"""Highlight two upper PROM-to-latch front-photo candidate bundles."""

from collections import deque
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
CONSTRAINT = HERE / 'photo-i7-constraint.json'
MANIFEST = HERE.parent / 'board/evidence/manifest.json'
OUT = HERE / 'results/photo-upper-bundle'

TRACKS = (
    dict(name='U17-to-U29', seed=(1311, 430), bounds=(1220, 373, 1322, 603),
         crop=(1100, 330, 1410, 710),
         observation='Single visible component approaches U29 and U17 pad regions.'),
    dict(name='U18-to-U30', seed=(652, 430), bounds=(542, 361, 662, 609),
         crop=(450, 330, 760, 710),
         observation='Threshold component merges two parallel tracks near U30 pads.'),
)


def run(out=OUT):
    config = json.loads(CONSTRAINT.read_text())
    source = (HERE / config['front_photo']).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['front_sha256']:
        raise ValueError('front photo hash changed')
    view = json.loads(MANIFEST.read_text())['views']['front']
    original = Image.open(source).transpose(Image.Transpose.ROTATE_270)
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x * original.width, y * original.height))
    frame = original.transform(tuple(config['back_rectified_size']), Image.Transform.QUAD,
                               quad, resample=Image.Resampling.BICUBIC).convert('RGB')
    pixels = frame.load()
    canvas = Image.new('RGB', (660, 450), '#10212a')
    draw = ImageDraw.Draw(canvas)
    records = []
    for index, track in enumerate(TRACKS):
        seed = track['seed']
        queue = deque([seed])
        seen = {seed}
        while queue:
            x, y = queue.popleft()
            for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if not (0 <= xx < frame.width and 0 <= yy < frame.height) or (xx, yy) in seen:
                    continue
                r, g, b = pixels[xx, yy]
                if g > 115 and b > 115 and g > r * 1.05:
                    seen.add((xx, yy))
                    queue.append((xx, yy))
        bounds = (min(x for x, y in seen), min(y for x, y in seen),
                  max(x for x, y in seen), max(y for x, y in seen))
        if bounds != track['bounds']:
            raise ValueError(f"{track['name']} bright component changed: {bounds}")
        crop = frame.crop(track['crop']).copy()
        cp = crop.load()
        left, top, right, bottom = track['crop']
        for x, y in seen:
            if left <= x < right and top <= y < bottom:
                cp[x - left, y - top] = (255, 60, 15)
        canvas.paste(crop, (10 + index * 330, 40))
        draw.text((10 + index * 330, 13), track['name'], fill='white')
        records.append(dict(name=track['name'], seed=seed, component_pixels=len(seen),
                            bounds=bounds, crop=track['crop'],
                            observation=track['observation']))
    draw.text((10, 427), 'Bright-pixel highlight is a photo aid, not continuity proof.', fill='white')
    out.mkdir(parents=True, exist_ok=True)
    canvas.save(out / 'candidate-front-tracks.jpg', quality=94)
    report = dict(status='photo-visible PROM-to-latch bundle candidates',
                  photo=str(Path(config['front_photo'])),
                  front_sha256=config['front_sha256'],
                  rectified_size=config['back_rectified_size'],
                  threshold='G>115 and B>115 and G>1.05*R, four-neighbour',
                  tracks=records,
                  limitations=[
                      'Dim gaps remain at the PROM pad ends; no pin-to-pin continuity was measured.',
                      'The U18 component merges two tracks at the threshold, so it is not a single net.',
                      'The latch output routes to U8 and their bit order are not established by this overlay.'])
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print([(track['name'], track['bounds'], track['component_pixels'])
           for track in result['tracks']])
