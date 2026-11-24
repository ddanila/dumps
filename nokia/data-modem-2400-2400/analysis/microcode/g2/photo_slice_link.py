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
SEGMENTS = (
    dict(id='I4-I1', seed=(3027, 1500), bounds=(3007, 1358, 3031, 1533),
         u8_pin='28 (I4)', u2_pin='13 (I1)', bits=(4, 1), color=(255, 20, 20)),
    dict(id='I6-I2', seed=(2972, 1500), bounds=(2934, 1342, 2977, 1537),
         u8_pin='26 (I6)', u2_pin='14 (I2)', bits=(6, 2), color=(255, 220, 20)),
)


def visible_segments(overlay):
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

    found = []
    colors = []
    for segment in SEGMENTS:
        seed = segment['seed']
        if not bright(*seed):
            raise ValueError(f'{segment["id"]}: track seed is not bright')
        queue, seen = deque([seed]), {seed}
        while queue:
            x, y = queue.popleft()
            for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if (0 <= xx < frame.width and 0 <= yy < frame.height and
                        (xx, yy) not in seen and bright(xx, yy)):
                    seen.add((xx, yy))
                    queue.append((xx, yy))
        bounds = (min(x for x, _ in seen), min(y for _, y in seen),
                  max(x for x, _ in seen), max(y for _, y in seen))
        if bounds != segment['bounds']:
            raise ValueError(f'{segment["id"]}: candidate segment changed: {bounds}')
        found.append(dict(id=segment['id'], seed=list(seed), bounds=list(bounds),
                          pixels=len(seen),
                          candidate_endpoints=[f'U8 pin {segment["u8_pin"]}, upper pad vicinity',
                                               f'U2 pin {segment["u2_pin"]}, lower pad vicinity'],
                          status='photo-visible segment with pad gaps; not measured continuity'))
        colors.append((seen, segment['color']))
    for seen, color in colors:
        for x, y in seen:
            pixels[x, y] = color
    overlay.parent.mkdir(parents=True, exist_ok=True)
    frame.crop((2900, 1290, 3140, 1580)).save(overlay, quality=94)
    return dict(segments=found,
                threshold='G>90, B>105, G>1.3*R; four-neighbor components')


def mismatch(instruction, bits):
    hi, lo = bits
    return bool(((instruction >> hi) ^ (instruction >> lo)) & 1)


def run(out):
    overlay = out.parent / 'photo-slice-link' / 'candidate.jpg'
    segments = visible_segments(overlay)
    _, base = fixture()
    _, bits = controller_stream()
    base['initial']['q'] = 5
    base['io']['read']['pc_sequences']['910'] = bits
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        for name, path in MAPPINGS.items():
            mapping = mapped(path)
            rows = decode(mapping)
            static_by_link = {link['id']: sum(not row['unused'] and
                              mismatch(row['i'], link['bits']) for row in rows)
                              for link in SEGMENTS}
            static_either = sum(not row['unused'] and
                                any(mismatch(row['i'], link['bits']) for link in SEGMENTS)
                                for row in rows)
            result = execute(mapping, base, 1580, mode='integrated',
                             out=Path(temporary) / name, trace_limit=1580)
            trace = [json.loads(line) for line in
                     (Path(temporary) / name / 'trace.jsonl').read_text().splitlines()]
            if not result['clean'] or len(trace) != 1580:
                raise ValueError(f'{name} controller-fed execution did not complete')
            executed_by_link = {link['id']: sum(mismatch(row['instruction_i'], link['bits'])
                                for row in trace) for link in SEGMENTS}
            differing = [row for row in trace if any(
                mismatch(row['instruction_i'], link['bits']) for link in SEGMENTS)]
            cases.append(dict(mapping=name,
                              distinct_nonblank_words=len([row for row in rows if not row['unused']]),
                              static_mismatch_by_link=static_by_link,
                              static_mismatch_either=static_either,
                              executed_cycles=len(trace),
                              executed_mismatch_by_link=executed_by_link,
                              executed_mismatch_either=len(differing),
                              executed_mismatch_pcs={f'{pc:03X}': count for pc, count in
                                  sorted(Counter(row['pc'] for row in differing).items())},
                              trace_digest=result['trace_digest']))
    sources = [Path(__file__), FRONT, MANIFEST,
               HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
               HERE/'photo_mapping_stream_screen.py',
               HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
               *MAPPINGS.values()]
    report = dict(status='conditional photo link and shared-instruction compatibility test',
                  visible_segments=segments,
                  pin_interpretation='U8 and U2 markings have the same orientation. Using the Am2901 P-40/D-40 top-view pinout and existing U2 pin attribution, the facing pads are candidate U8.I4 to U2.I1 and U8.I6 to U2.I2.',
                  test='If both slices receive one common 9-bit I word and the candidate nets are real, I4=I1 and I6=I2 must hold on every executed word. The current mappings do not enforce these equalities.',
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
    print([(x['mapping'], x['static_mismatch_by_link'], x['executed_mismatch_by_link'])
           for x in report['cases']])
