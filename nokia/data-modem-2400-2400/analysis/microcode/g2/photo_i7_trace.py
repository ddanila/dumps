"""Render the candidate front-side U11 E4 to U6 D0 trace for inspection."""
from collections import deque
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

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


def render_shared_enable(out):
    config = json.loads(CONSTRAINT.read_text())
    source = (HERE / config['back_photo']).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['back_sha256']:
        raise ValueError('back photograph hash mismatch')
    view = json.loads(MANIFEST.read_text())['views']['back']
    original = ImageOps.flip(Image.open(source))
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x * original.width, y * original.height))
    frame = original.transform(tuple(config['back_rectified_size']), Image.Transform.QUAD,
                               quad, resample=Image.Resampling.BICUBIC)
    pixels = frame.load()
    x, y = config['candidate_shared_enable_route']['back_track_seed_rectified']
    queue = deque([(x, y)])
    seen = {(x, y)}
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= xx < frame.width and 0 <= yy < frame.height) or (xx, yy) in seen:
                continue
            r, g, b = pixels[xx, yy]
            if g > 120 and b > 120 and g > r * 1.05:
                seen.add((xx, yy))
                queue.append((xx, yy))
    bounds = [min(x for x, y in seen), min(y for x, y in seen),
              max(x for x, y in seen), max(y for x, y in seen)]
    if bounds != config['candidate_shared_enable_route']['bright_component_bounds_at_threshold_120']:
        raise ValueError(f'back photo threshold component changed: {bounds}')
    colored = frame.copy()
    cp = colored.load()
    for x, y in seen:
        cp[x, y] = (255, 70, 30)
    crop = colored.crop((530, 1230, 1380, 1360))
    canvas = Image.new('RGB', (850, 215), '#10212a')
    canvas.paste(crop, (0, 48))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 15), 'Candidate shared E4 trace: U11 pin 18 to U10 pin 18', fill='white')
    draw.text((16, 190), 'Photo threshold is a tracing aid; the signal driver is not identified.',
              fill='white')
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=94)
    return bounds


def render_prom_data(out):
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
    x, y = config['candidate_prom_data_route']['front_track_seed_rectified']
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
    if bounds != config['candidate_prom_data_route']['bright_component_bounds_at_threshold_115']:
        raise ValueError(f'front PROM-data threshold component changed: {bounds}')
    colored = frame.copy()
    cp = colored.load()
    for x, y in seen:
        cp[x, y] = (255, 70, 30)
    crop = colored.crop((1060, 1300, 1460, 1720))
    canvas = Image.new('RGB', (800, 520), '#10212a')
    canvas.paste(crop.resize((800, 420)), (0, 62))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 18), 'Candidate route: U10 pin 17 (D7) to U5 pin 4 (D1)', fill='white')
    draw.text((16, 490), 'Adjacent pin 18 is E4; this is a separate candidate data route.',
              fill='white')
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=94)
    return bounds


def render_a2(out):
    config = json.loads(CONSTRAINT.read_text())
    source = (HERE / config['back_photo']).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['back_sha256']:
        raise ValueError('back photograph hash mismatch')
    view = json.loads(MANIFEST.read_text())['views']['back']
    original = ImageOps.flip(Image.open(source))
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x * original.width, y * original.height))
    frame = original.transform(tuple(config['back_rectified_size']), Image.Transform.QUAD,
                               quad, resample=Image.Resampling.BICUBIC)
    pixels = frame.load()
    x, y = config['candidate_a2_route']['back_track_seed_rectified']
    queue = deque([(x, y)])
    seen = {(x, y)}
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= xx < frame.width and 0 <= yy < frame.height) or (xx, yy) in seen:
                continue
            r, g, b = pixels[xx, yy]
            if g > 120 and b > 120 and g > r * 1.05:
                seen.add((xx, yy))
                queue.append((xx, yy))
    bounds = [min(x for x, y in seen), min(y for x, y in seen),
              max(x for x, y in seen), max(y for x, y in seen)]
    if bounds != config['candidate_a2_route']['bright_component_bounds_at_threshold_120']:
        raise ValueError(f'A2 photo threshold component changed: {bounds}')
    colored = frame.copy()
    cp = colored.load()
    for x, y in seen:
        cp[x, y] = (255, 70, 30)
    crop = colored.crop((1200, 1540, 3520, 1710))
    canvas = Image.new('RGB', (2320, 250), '#10212a')
    canvas.paste(crop, (0, 43))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 13), 'Candidate route: U5 Q1 to U2 A2; U5 D1 appears to receive U10 D7', fill='white')
    draw.text((16, 220), 'Bright-pixel trace is an inspection aid; the U2 pad connection has a dim gap.',
              fill='white')
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=94)
    return bounds


def render_a0(out):
    config = json.loads(CONSTRAINT.read_text())
    source = (HERE / config['back_photo']).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['back_sha256']:
        raise ValueError('back photograph hash mismatch')
    view = json.loads(MANIFEST.read_text())['views']['back']
    original = ImageOps.flip(Image.open(source))
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x * original.width, y * original.height))
    frame = original.transform(tuple(config['back_rectified_size']), Image.Transform.QUAD,
                               quad, resample=Image.Resampling.BICUBIC)
    pixels = frame.load()
    x, y = config['candidate_shared_i7_a0_route']['back_track_seed_rectified']
    queue = deque([(x, y)])
    seen = {(x, y)}
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= xx < frame.width and 0 <= yy < frame.height) or (xx, yy) in seen:
                continue
            r, g, b = pixels[xx, yy]
            if g > 120 and b > 120 and g > r * 1.05:
                seen.add((xx, yy))
                queue.append((xx, yy))
    bounds = [min(x for x, y in seen), min(y for x, y in seen),
              max(x for x, y in seen), max(y for x, y in seen)]
    if bounds != config['candidate_shared_i7_a0_route']['bright_component_bounds_at_threshold_120']:
        raise ValueError(f'A0 photo threshold component changed: {bounds}')
    colored = frame.copy()
    cp = colored.load()
    for x, y in seen:
        cp[x, y] = (255, 70, 30)
    crop = colored.crop((650, 1540, 3450, 1730))
    canvas = Image.new('RGB', (2800, 270), '#10212a')
    canvas.paste(crop, (0, 42))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 12), 'Candidate route: U6 Q0 to U2 A0; Q0 also appears to feed I7', fill='white')
    draw.text((16, 245), 'The U2 pad connection has a dim gap; this remains a photo interpretation.',
              fill='white')
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=94)
    return bounds


if __name__ == '__main__':
    target = HERE / 'results/photo-i7-probe/candidate-front-route.jpg'
    print('highlight bounds:', render(target))
    target = HERE / 'results/photo-i7-probe/candidate-enable-bus.jpg'
    print('shared enable highlight bounds:', render_shared_enable(target))
    target = HERE / 'results/photo-i7-probe/candidate-u10-d7-latch.jpg'
    print('PROM data highlight bounds:', render_prom_data(target))
    target = HERE / 'results/photo-i7-probe/candidate-a2-route.jpg'
    print('A2 highlight bounds:', render_a2(target))
    target = HERE / 'results/photo-i7-probe/candidate-a0-route.jpg'
    print('A0 highlight bounds:', render_a0(target))
