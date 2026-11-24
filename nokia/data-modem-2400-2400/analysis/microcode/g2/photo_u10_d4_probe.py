"""Check a visible U10 D4-to-U5 Q3 candidate and a hypothetical I1 route."""
import hashlib
import json
import sys
import tempfile
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from instruction_bit_neighborhood import after_input_groups, score_groups
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

FRONT = HERE/'../../../photos/PXL_20261123_114926601.jpg'
MANIFEST = HERE.parent/'board/evidence/manifest.json'
SEED = (1131, 1400)
EXPECTED_BOUNDS = (1130, 1341, 1152, 1662)


def visible_segment(overlay=None):
    view = json.loads(MANIFEST.read_text())['views']['front']
    if hashlib.sha256(FRONT.read_bytes()).hexdigest() != view['source_sha256']:
        raise ValueError('front photograph changed')
    original = Image.open(FRONT).transpose(Image.Transpose.ROTATE_270)
    quad = tuple(value for x, y in view['quadrilateral_normalized_UL_LL_LR_UR']
                 for value in (x*original.width, y*original.height))
    frame = original.transform((4000, 2000), Image.Transform.QUAD, quad,
                               resample=Image.Resampling.BICUBIC)
    pixels = frame.load()
    def bright(x, y):
        r, g, b = pixels[x, y]
        return g > 115 and b > 115 and g > r*1.05
    if not bright(*SEED):
        raise ValueError('candidate track seed is no longer bright')
    queue = deque([SEED])
    seen = {SEED}
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if (0 <= xx < frame.width and 0 <= yy < frame.height and
                    (xx, yy) not in seen and bright(xx, yy)):
                seen.add((xx, yy))
                queue.append((xx, yy))
    bounds = (min(x for x, _ in seen), min(y for _, y in seen),
              max(x for x, _ in seen), max(y for _, y in seen))
    if bounds != EXPECTED_BOUNDS:
        raise ValueError(f'candidate track bounds changed: {bounds}')
    if overlay is not None:
        for x, y in seen:
            pixels[x, y] = (255, 20, 20)
        draw = ImageDraw.Draw(frame)
        for x, y, label, tx, ty in ((1131, 1345, 'U10.14 D4', 1155, 1315),
                                    (1095, 1665, 'U5.10 GND', 1240, 1550),
                                    (1131, 1665, 'U5.9 Q3', 1240, 1590),
                                    (1168, 1665, 'U5.8 D3', 1240, 1630)):
            draw.ellipse((x-6, y-6, x+6, y+6), outline='yellow', width=3)
            draw.line((x+7, y, tx-8, ty+5), fill='yellow', width=1)
            draw.text((tx, ty), label, fill='yellow', stroke_width=1,
                      stroke_fill='black')
        overlay.parent.mkdir(parents=True, exist_ok=True)
        frame.crop((1060, 1290, 1350, 1720)).save(overlay, quality=94)
    return dict(source='U10 pin 14, PROM data bit 4',
                candidate_destination='U5 pin 9, fourth Q output',
                adjacent_pin='U5 pin 8, fourth D input, is one pad to the right and is not reached by this bright component',
                electrical_question='Two output pins may share a bus only under compatible enable timing; the photo does not establish that timing or any driver-to-I1 route.',
                threshold='G>115, B>115, G>1.05*R; four-neighbor component',
                seed=list(SEED), bounds=list(bounds), pixel_count=len(seen),
                status='photo-visible-segment-near-pads, not continuity proof')


def run(out):
    segment = visible_segment(out.parent/'photo-u10-d4-probe'/'corrected-pad.jpg')
    _, scenario = fixture()
    _, bits = controller_stream()
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = bits
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        trace_path = Path(temporary)
        for name, path in MAPPINGS.items():
            for source in ('10.4', '!10.4'):
                mapping = mapped(path)
                mapping['fields']['i']['bits'][1] = source
                result = execute(mapping, scenario, 512, mode='integrated',
                                 out=trace_path, trace_limit=512)
                trace = [json.loads(line) for line in
                         (trace_path/'trace.jsonl').read_text().splitlines()]
                metrics = score_groups(after_input_groups(trace))
                metrics.pop('first_8_groups')
                cases.append(dict(mapping=name, hypothetical_i1_source=source,
                                  clean=result['clean'],
                                  input_visits=result['address_counts'].get(0x38E, 0),
                                  selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                  trace_digest=result['trace_digest'], **metrics))
    if (len(cases) != 10 or any(not row['clean'] or row['input_visits'] != 39 or
                               row['group_count'] != 38 for row in cases)):
        raise ValueError('candidate-path execution changed')
    sources = [Path(__file__), FRONT, MANIFEST,
               HERE/'instruction_bit_neighborhood.py',
               HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
               HERE/'photo_mapping_stream_screen.py', HERE/'controller_bit_dispatch.py',
               ASSUMED/'execute.py', *MAPPINGS.values()]
    report = dict(status='photo candidate output-to-output route plus untraced hypothetical I1 assignment',
                  visible_segment=segment,
                  candidate_test='The tested I1=10.4/!10.4 substitutions are counterfactual signal assignments. U5 Q3 to Am2901 I1 and the output-enable timing are untraced.',
                  fixture=dict(initial_q=5, initial_ram=[0]*16, cycles=512,
                               controller_bits_offered=len(bits), hypothetical_input_pc='38E'),
                  cases=cases,
                  limitations=['The source/destination pad gaps, output-enable timing and U5 Q3 continuation are unresolved; this is not a recovered instruction-bit mapping.',
                               'The photographed destination is U5 Q3, not its D3 input. These runs do not model PROM-output and latch-output contention.',
                               'One PROM bit is tried at one I input. Other pin routes, modes, startup states and ROM gates remain open.',
                               'Candidate ALU-Y output sites have no traced connection to the DAC08HP.'],
                  source_sha256={str(path.resolve().relative_to(HERE.parents[2].resolve())):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-u10-d4-probe.json')
    print(report['visible_segment'],
          [(x['mapping'], x['hypothetical_i1_source'], x['selected_rom_reads'])
           for x in report['cases']])
