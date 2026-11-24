"""Render the candidate front-side U11 E4 to U6 D0 trace for inspection."""
from collections import deque
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
CONSTRAINT = HERE / 'photo-i7-constraint.json'
MANIFEST = HERE.parent / 'board/evidence/manifest.json'


def render(out):
    config = json.loads(CONSTRAINT.read_text())
    source = (HERE / config['front_photo']).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['front_sha256']:
        raise ValueError('front photograph hash mismatch')
    view = json.loads(MANIFEST.read_text())['views']['front']
    original = Image.open(source).transpose(Image.Transpose.ROTATE_270)
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x * original.width, y * original.height))
    frame = original.transform(tuple(config['back_rectified_size']), Image.Transform.QUAD,
                               quad, resample=Image.Resampling.BICUBIC)
    pixels = frame.load()
    x, y = config['candidate_input_route']['front_track_seed_rectified']
    queue = deque([(x, y)])
    seen = {(x, y)}
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= xx < frame.width and 0 <= yy < frame.height) or (xx, yy) in seen:
                continue
            r, g, b = pixels[xx, yy]
            if g > 115 and b > 115 and g > r * 1.05:
                seen.add((xx, yy))
                queue.append((xx, yy))
    bounds = [min(x for x, y in seen), min(y for x, y in seen),
              max(x for x, y in seen), max(y for x, y in seen)]
    if bounds != config['candidate_input_route']['bright_component_bounds_at_threshold_115']:
        raise ValueError(f'photo threshold component changed: {bounds}')
    colored = frame.copy()
    cp = colored.load()
    for x, y in seen:
        cp[x, y] = (255, 70, 30)
    crop = colored.crop((380, 1300, 790, 1720))
    canvas = Image.new('RGB', (820, 520), '#10212a')
    canvas.paste(crop.resize((820, 420)), (0, 62))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 18), 'Candidate route: U11 pin 18 (E4) to U6 pin 3 (D0)', fill='white')
    draw.text((16, 490), 'Threshold highlight is a photo aid, not a continuity measurement.',
              fill='white')
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=94)
    return bounds


if __name__ == '__main__':
    target = HERE / 'results/photo-i7-probe/candidate-front-route.jpg'
    print('highlight bounds:', render(target))
