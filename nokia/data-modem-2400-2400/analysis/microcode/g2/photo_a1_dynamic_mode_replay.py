"""Replay held-A1 controller frame changes into a candidate DSC DAC path."""

import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_cd4094_order import shift_four_bytes
from photo_controller_mode_decode import decode_chip1
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CONTROLLER_REPORT = HERE / 'results/a1-counter-phase.json'
DSC_OSC_HZ = 14_400_000
CONTROLLER_OSC_HZ = 11_980_800
CONTROLLER_CLOCKS_PER_MACHINE_CYCLE = 12
DSC_MICROCYCLE_DIVISOR = 1
MICROINSTRUCTIONS_PER_LOOP = 4
VISITS_PER_DAC_SAMPLE = 375
SAMPLE_HZ = 9600
CYCLES = 220_000


def tone_fit(values, frequency):
    n = len(values)
    mean = sum(values) / n
    centered = [value - mean for value in values]
    angles = [2 * math.pi * frequency * i / SAMPLE_HZ for i in range(n)]
    cosines = [math.cos(angle) for angle in angles]
    sines = [math.sin(angle) for angle in angles]
    mc = sum(cosines) / n
    ms = sum(sines) / n
    c = [v - mc for v in cosines]
    s = [v - ms for v in sines]
    cc = sum(v * v for v in c)
    ss = sum(v * v for v in s)
    cs = sum(a * b for a, b in zip(c, s))
    yc = sum(a * b for a, b in zip(centered, c))
    ys = sum(a * b for a, b in zip(centered, s))
    det = cc * ss - cs * cs
    var = sum(v * v for v in centered)
    if not det or not var:
        return 0.0
    a = (yc * ss - ys * cs) / det
    b = (ys * cc - yc * cs) / det
    return (a * yc + b * ys) / var


def tone_summary(values):
    scores = {f: tone_fit(values, f) for f in range(1000, 3001, 10)}
    peak = max(scores, key=scores.get)
    return dict(samples=len(values), distinct_codes=len(set(values)),
                peak_hz=peak, peak_r2=round(scores[peak], 6),
                r2_1800=round(scores[1800], 6),
                r2_2100=round(scores[2100], 6))


def inspect_trace(path, rom, inputs, switch_visit):
    pc127_visits = 0
    pc129_visits = 0
    phase = 3
    step = None
    captures = []
    boundary = []
    with path.open() as stream:
        for line in stream:
            if '"pc": 295' not in line and '"pc": 297' not in line:
                continue
            row = json.loads(line)
            if row['pc'] == 0x127:
                expected = inputs[min(pc127_visits, len(inputs) - 1)]
                event = row['external_read']
                if (event['value'] != expected or
                        event['visit'] != pc127_visits):
                    raise AssertionError(('D127 sequence', pc127_visits, event))
                step = expected
                if switch_visit - 2 <= pc127_visits <= switch_visit + 2:
                    boundary.append(dict(visit=pc127_visits,
                                         cycle=row['cycle'],
                                         d127=f'{step:02X}'))
                pc127_visits += 1
            elif row['pc'] == 0x129:
                if step is None or pc129_visits >= pc127_visits:
                    raise AssertionError('PC129 preceded PC127')
                phase = (phase + step) & 255
                address = 256 + phase
                selected = row['external_read']
                value = rom[address]
                y = (phase - value) & 255
                if (selected['address'] != address or
                        selected['value'] != value or
                        row['alu']['y'] != y):
                    raise AssertionError(('phase/ROM/Y recurrence',
                                          pc129_visits, row))
                pc129_visits += 1
                if (pc129_visits - 1) % VISITS_PER_DAC_SAMPLE == 0:
                    captures.append(dict(visit=pc129_visits,
                                         cycle=row['cycle'],
                                         step=f'{step:02X}',
                                         phase=f'{phase:02X}',
                                         dac_code=q_to_dac(y, 'swap_q4_q5')))
    if (pc127_visits != pc129_visits or
            pc127_visits <= switch_visit + 10_000 or
            len(boundary) != 5):
        raise AssertionError(('incomplete phase trace', pc127_visits,
                              pc129_visits, switch_visit, boundary))
    return captures, boundary, pc127_visits


def run(out=HERE / 'results/photo-a1-dynamic-mode-replay.json'):
    controller = json.loads(CONTROLLER_REPORT.read_text())
    if controller['controller_rom_sha256'] != (
            'daf854c513cd427664bb345f511afc2d38441e5002e4a85389d289aedbfc0038'):
        raise ValueError('controller ROM changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for held in controller['held_a1']:
        frames = [bytes(frame) for frame in held['frames']]
        chip1 = [shift_four_bytes(frame)[1]['q8_to_d0'] for frame in frames]
        decoded = [decode_chip1(raw) for raw in chip1]
        if (chip1 != [0xa1]*11 + [0x81] or
                decoded != [(1, 1, 0xb0)]*11 + [(1, 0, 0x88)]):
            raise AssertionError(('held controller frames changed',
                                  held['selector'], chip1))
        controller_cycles = (held['iteration_cycles'][11] -
                             held['iteration_cycles'][0])
        switch_visit = round(controller_cycles * DSC_OSC_HZ *
                             CONTROLLER_CLOCKS_PER_MACHINE_CYCLE /
                             (CONTROLLER_OSC_HZ * DSC_MICROCYCLE_DIVISOR *
                              MICROINSTRUCTIONS_PER_LOOP))
        inputs = [0xb0] * switch_visit + [0x88]
        scenario = hold_candidate(base)
        scenario['name'] += '; held-A1 frame bit5 change at controller cadence'
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
        scenario['io']['read']['pc_sequences'][str(0x12c)] = [
            shift_four_bytes(frames[0])[0]['q8_to_d0']]
        scenario['io']['read']['address']['bank_by_pc'] = {
            str(0x129): 256, str(0x12e): 256}
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=temporary, trace_limit=CYCLES)
            captures, boundary, visits = inspect_trace(
                Path(temporary) / 'trace.jsonl', rom, inputs, switch_visit)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x129) != visits or
                result['address_counts'].get(0x12e, 0) != 0):
            raise AssertionError(('DSC run incomplete', held['selector']))
        pre = [row['dac_code'] for row in captures if row['step'] == 'B0']
        post = [row['dac_code'] for row in captures if row['step'] == '88']
        before = tone_summary(pre)
        after = tone_summary(post)
        if (before['samples'] < 60 or after['samples'] < 60 or
                before['peak_hz'] != 1800 or after['peak_hz'] != 2100 or
                before['r2_1800'] <= before['r2_2100'] or
                after['r2_2100'] <= after['r2_1800']):
            raise AssertionError(('dynamic candidate tone changed',
                                  held['selector'], before, after))
        cases.append(dict(selector=held['selector'],
                          controller_cycle_delta=controller_cycles,
                          switch_pc127_visit=switch_visit,
                          first_12_chip1=[f'{v:02X}' for v in chip1],
                          d127_before='B0', d127_after='88',
                          pc127_and_pc129_visits=visits,
                          switch_trace=boundary,
                          before=before, after=after,
                          first_8_pre_dac_codes=[f'{v:02X}' for v in pre[:8]],
                          first_8_post_dac_codes=[f'{v:02X}' for v in post[:8]],
                          trace_digest=result['trace_digest']))
    paths = [Path(__file__), CONTROLLER_REPORT, ROM,
             HERE / 'a1_counter_phase.py',
             HERE / 'photo_controller_mode_decode.py',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(
        status='held-A1 frame sequence changes photo-compatible DSC phase walk without resetting microcode',
        fixture=dict(controller='unchanged 8031 ROM held-A1 frames, four selector classes',
                     controller_clock='11.9808 MHz oscillator / 12 clocks per machine cycle',
                     dsc_clock='14.4 MHz oscillator / one oscillator period per microinstruction',
                     pc127_visits_per_loop=1,
                     sample_gate='one PC129 Y capture per 375 visits, 9600 Hz',
                     d127_decode='chip1 bit5 drives B0 before and 88 after; photo-compatible but untraced fan-out/inversion',
                     d12c='logical chip0 Q8→D0, held 7A',
                     rom_bank='upper at PC129', mapping='q3 photo-swapped',
                     dac_bus='Y129→LS273 ordered; Q4/Q5 swapped to DAC08'),
        cases=cases,
        limitations=['The chip1 decoder, PC127 route, ROM bank, microcycle rate, DAC bus and 9600 Hz capture gate are hypotheses, not traced board connections.',
                     'Controller-to-DSC timing is aligned by iteration-completion cycle differences; no physical handshake or common clock phase is known.',
                     'Controller A1 is held by suppressing a timer-underflow fixture; its natural-duration waveform is not established.',
                     'The projected DAC codes are not measured line output and contain no USART dibit modulation or receive/echo path.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-a1-dynamic-mode-replay.json')
    args = parser.parse_args()
    for case in run(args.out)['cases']:
        print(case['selector'], case['switch_pc127_visit'],
              case['before']['peak_hz'], case['after']['peak_hz'])
