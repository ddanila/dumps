"""Screen a photographed U8/U2 facing-pin candidate against shared-I mappings."""
import hashlib
import json
import sys
import tempfile
from collections import Counter, deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import decode, save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

FRONT = HERE / '../../../photos/PXL_20261123_114926601.jpg'
MANIFEST = HERE.parent / 'board/evidence/manifest.json'
SEED = (3027, 1500)
BOUNDS = (3007, 1358, 3031, 1533)


def visible_segment(overlay):
    view = json.loads(MANIFEST.read_text())['views']['front']
    if hashlib.sha256(FRONT.read_bytes()).hexdigest() != view['source_sha256']:
        raise ValueError('front photograph changed')
    original = Image.open(FRONT).transpose(Image.Transpose.ROTATE_270)
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x * original.width, y * original.height))
    frame = original.transform((4000, 2000), Image.Transform.QUAD, quad,
                               resample=Image.Resampling.BICUBIC)
    pixels = frame.load()

    def bright(x, y):
        r, g, b = pixels[x, y]
        return g > 90 and b > 105 and g > r * 1.3

    if not bright(*SEED):
        raise ValueError('track seed is not bright')
    queue, seen = deque([SEED]), {SEED}
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (0 <= xx < frame.width and 0 <= yy < frame.height and
                    (xx, yy) not in seen and bright(xx, yy)):
                seen.add((xx, yy))
                queue.append((xx, yy))
    bounds = (min(x for x, _ in seen), min(y for _, y in seen),
              max(x for x, _ in seen), max(y for _, y in seen))
    if bounds != BOUNDS:
        raise ValueError(f'candidate segment changed: {bounds}')
    for x, y in seen:
        pixels[x, y] = (255, 20, 20)
    overlay.parent.mkdir(parents=True, exist_ok=True)
    frame.crop((2920, 1290, 3140, 1580)).save(overlay, quality=94)
    return dict(seed=list(SEED), bounds=list(bounds), pixels=len(seen),
                threshold='G>90, B>105, G>1.3*R; four-neighbor component',
                candidate_endpoints=['U8 pin 28 (I4), upper pad vicinity',
                                     'U2 pin 13 (I1), lower pad vicinity'],
                status='photo-visible segment with pad gaps; not measured continuity')


def mismatch(instruction):
    return bool(((instruction >> 1) ^ (instruction >> 4)) & 1)


def run(out):
    overlay = out.parent / 'photo-slice-link' / 'candidate.jpg'
    segment = visible_segment(overlay)
    _, base = fixture()
    _, bits = controller_stream()
    base['initial']['q'] = 5
    base['io']['read']['pc_sequences']['910'] = bits
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        for name, path in MAPPINGS.items():
            mapping = mapped(path)
            rows = decode(mapping)
            static = [row for row in rows if not row['unused'] and mismatch(row['i'])]
            result = execute(mapping, base, 1580, mode='integrated',
                             out=Path(temporary) / name, trace_limit=1580)
            trace = [json.loads(line) for line in
                     (Path(temporary) / name / 'trace.jsonl').read_text().splitlines()]
            if not result['clean'] or len(trace) != 1580:
                raise ValueError(f'{name} controller-fed execution did not complete')
            differing = [row for row in trace if mismatch(row['instruction_i'])]
            cases.append(dict(mapping=name,
                              distinct_nonblank_words=len([row for row in rows if not row['unused']]),
                              static_mismatch_words=len(static),
                              executed_cycles=len(trace),
                              executed_mismatch_cycles=len(differing),
                              executed_mismatch_pcs={f'{pc:03X}': count for pc, count in
                                  sorted(Counter(row['pc'] for row in differing).items())},
                              trace_digest=result['trace_digest']))
    sources = [Path(__file__), FRONT, MANIFEST,
               HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
               HERE/'photo_mapping_stream_screen.py',
               HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
               *MAPPINGS.values()]
    report = dict(status='conditional photo link and shared-instruction compatibility test',
                  visible_segment=segment,
                  pin_interpretation='U8 and U2 markings have the same orientation. Using the Am2901 P-40/D-40 top-view pinout and existing U2 pin attribution, the facing pads are candidate U8.I4 and U2.I1.',
                  test='If both slices receive one common 9-bit I word and the candidate net is real, I4 and I1 must agree on every executed word. The current mappings do not enforce that equality.',
                  fixture=dict(cycles=1580, initial_q=5, controller_bits=len(bits)),
                  cases=cases,
                  limitations=['A bright track with dim pad gaps is not a continuity measurement.',
                               'A real cross-link could mean distinct instruction words for U8 and U2, rather than an impossible board.',
                               'The compatibility check does not execute a split-slice model or establish the source of either pin.'],
                  source_sha256={str(path.resolve().relative_to(HERE.parents[2].resolve())):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/photo-slice-link.json')
    print([(x['mapping'], x['static_mismatch_words'], x['executed_mismatch_cycles'])
           for x in report['cases']])
