"""Use candidate photo traces to constrain ALU register roles, then run variants."""
import argparse
from collections import deque
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
BOARD = HERE.parent / 'board'
sys.path[:0] = [str(ASSUMED), str(BOARD)]
from common import decode, read, save
from analyze import graph
from phase_add_screen import cyclic_components
from all_rom_gate_cycles import cyclic_write_counts
from photo_hypotheses import candidate, experiment, scenario


def check_mapping(mapping, constraints):
    checks = []
    chip = constraints['bundle_assumption']['source']
    bits = mapping['fields']['b']['bits']
    for trace in constraints['traces']:
        token = bits[trace['target_bit']]
        checks.append(dict(trace=trace['id'], mapped_bit=token,
                           lane_compatible=token.lstrip('!').split('.')[0] == chip,
                           identity_permutation_match=token == f'{chip}.{trace["source_bit"]}'))
    return dict(checks=checks, lane_compatible=all(c['lane_compatible'] for c in checks),
                identity_permutation_match=all(c['identity_permutation_match'] for c in checks))


def swapped(mapping):
    result = deepcopy(mapping)
    result['name'] += '-photo-ab-swapped'
    result['fields']['a'], result['fields']['b'] = result['fields']['b'], result['fields']['a']
    for field in ('a', 'b'):
        result['fields'][field]['status'] = 'hypothesis'
        result['fields'][field]['evidence'] = (
            'photo-b-constraints.json suggests U6 drives U2 B1-B3, assuming the U11/U6 bundle. '
            'Swapping the full A/B fields is an experiment; B0, A wiring and PROM/register bit order remain untraced.')
    if 'register' in result['fields']:
        result['fields']['register'] = deepcopy(result['fields']['b'])
    result['photo_constraint_scope'] = 'B1-B3 source-lane constraint only; full swap and unchanged instruction field remain hypotheses.'
    return result


def run(out, cycles):
    constraints = read(HERE / 'photo-b-constraints.json')
    photo = (HERE / constraints['source_photo']).resolve()
    if hashlib.sha256(photo.read_bytes()).hexdigest() != constraints['source_sha256']:
        raise ValueError('source photograph hash mismatch')
    catalog = read(ASSUMED / 'program-reading.json')
    mappings = {name: read(ASSUMED / path) for name, path in catalog['profiles'].items()}
    old_checks = {name: check_mapping(mapping, constraints) for name, mapping in mappings.items()}
    out.mkdir(parents=True, exist_ok=True)
    fits = read(ASSUMED / 'results/rom-gate-study/report.json')['fits']
    variants = {}
    for name in ('q1', 'q2', 'q3', 'q4'):
        mapping = swapped(mappings[name])
        label = name + '-photo-swapped'
        path = out / (label + '.json')
        save(path, mapping)
        rows = decode(mapping)
        flow = graph(rows, read(ASSUMED / catalog['scenario']), include_states=True)
        if flow['exceptions']:
            raise ValueError(flow['exceptions'])
        cyclic = {state[0] for group in cyclic_components(flow['state_edges']) for state in group}
        board = candidate(label, mapping_path=path)
        runs = []
        for fixture in (0, 1, 'pulse17'):
            report, trace, _ = experiment(board, scenario(fixture), cycles)
            report['fixture'] = fixture
            runs.append(report)
            with (out / f'{label}-{fixture}.csv').open('w') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(trace[0]), lineterminator='\n')
                writer.writeheader()
                writer.writerows(trace)
        variants[label] = dict(photo_check=check_mapping(mapping, constraints), runs=runs,
                               cyclic_d_register_writes=cyclic_write_counts(rows, fits, cyclic))
    sources = [HERE / 'photo-b-constraints.json', ASSUMED / 'program-reading.json',
               ASSUMED / catalog['scenario'], ASSUMED / 'results/rom-gate-study/report.json',
               *[ASSUMED / path for path in catalog['profiles'].values()]]
    report = dict(status='photo-constrained-hypotheses-not-G2-acceptance',
                  source_photo_sha256=constraints['source_sha256'],
                  source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sources},
                  existing_profiles=old_checks, variants=variants,
                  interpretation='Under the U11-to-U6 bundle assumption, the three candidate B-input traces conflict with the B-source lane in q1-q4 and fitted_original. fitted_swapped agrees. Four new full A/B swaps retain the independent source-field variants; they also agree with the three constraints. This is not a unique recovered instruction decode.',
                  limitations=constraints['limitations'] + [
                      'The complete A/B swap is broader than the three photo constraints.',
                      'Runs use the earlier literal-branch, external TEST/D/carry, and fetch/execute schedule assumptions.',
                      'Neither a running transmitter nor a controller-driven handshake is demonstrated.'])
    save(out / 'report.json', report)
    return report


def render(out):
    """Optional Pillow-only visual aid; masks are not accepted as proof of a net."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    config = read(HERE / 'photo-b-constraints.json')
    source = HERE / config['source_photo']
    if hashlib.sha256(source.read_bytes()).hexdigest() != config['source_sha256']:
        raise ValueError('source photograph hash mismatch')
    manifest = read(BOARD / 'evidence/manifest.json')['views']['back']
    im = ImageOps.flip(Image.open(source))
    quad = tuple(v for x, y in manifest['quadrilateral_normalized_UL_LL_LR_UR']
                 for v in (x*im.width, y*im.height))
    im = im.transform(tuple(config['rectified_size']), Image.Transform.QUAD, quad,
                      resample=Image.Resampling.BICUBIC)
    pixels = im.load()
    colored = im.copy()
    destination = colored.load()
    for trace in config['traces']:
        x, y = trace['seed']
        _, x, y = max((pixels[xx, yy][1], xx, yy)
                      for xx in range(x-4, x+5) for yy in range(y-2, y+3))
        queue = deque([(x, y)])
        seen = {(x, y)}
        while queue:
            x, y = queue.popleft()
            destination[x, y] = tuple(trace['color'])
            for xx, yy in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                if not (0 <= xx < im.width and 0 <= yy < im.height) or (xx, yy) in seen:
                    continue
                r, g, b = pixels[xx, yy]
                if g > 120 and b > 120 and g > r*1.05:
                    seen.add((xx, yy))
                    queue.append((xx, yy))
        if len(seen) > 100000:
            raise ValueError('tracing mask merged too much of the board')
    crop = colored.crop((400, 1480, 2980, 1725))
    canvas = Image.new('RGB', (2580, 440), '#11202b')
    canvas.paste(crop, (0, 90))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Monaco.ttf', 22)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 15), 'Candidate visible routes: U6 register outputs to U2 B-address inputs', fill='white', font=font)
    draw.text((20, 48), 'Threshold coloring is a tracing aid; dim gaps and PROM-to-register bit order remain unresolved.', fill='white', font=font)
    for i, trace in enumerate(config['traces']):
        draw.text((20+850*i, 350), f'{trace["id"]}: {trace["source"]} {trace["source_port"]} -> {trace["target"]} {trace["target_port"]}',
                  fill=tuple(trace['color']), font=font)
    draw.text((20, 395), 'Candidate photo interpretation, not a continuity measurement. Original photograph is unchanged.', fill='white', font=font)
    canvas.save(out, quality=95)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'results/photo-b-constraints')
    parser.add_argument('--cycles', type=int, default=128)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error('--cycles must be positive')
    report = run(args.out, args.cycles)
    if args.render:
        render(args.out / 'candidate-traces.jpg')
    print('Existing lane-compatible profiles:', [n for n, r in report['existing_profiles'].items() if r['lane_compatible']])
    for name, variant in report['variants'].items():
        print(name, variant['cyclic_d_register_writes'],
              [(r['fixture'], r['max_known_ram_bytes']) for r in variant['runs']])


if __name__ == '__main__':
    main()
