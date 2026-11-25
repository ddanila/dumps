"""Replay upper-slice D4 controller data through two LS273 clock hypotheses."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from controller_bit_dispatch import controller_stream
from dac08_latch_probe import capture, execute_trace, photo_b5
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

CLOCK_SITES = (0x38E, 0x39E)
LOOP_WORDS = 12
SAMPLES_PER_BIT = 8


def trial(mapping, base, bits):
    case = copy.deepcopy(base)
    case['initial']['q'] = 5
    offered = [16 * bit for bit in bits for _ in range(SAMPLES_PER_BIT)]
    case['io']['read']['pc_sequences']['910'] = offered
    # First input at cycle 49; 1024 inputs occupy cycles 49..12325.
    cycles = 49 + LOOP_WORDS * len(offered)
    result, trace = execute_trace(mapping, case, cycles)
    inputs = [row for row in trace if row['pc'] == 0x38E]
    if len(inputs) != len(offered) or [row['external_read']['value'] for row in inputs] != offered:
        raise ValueError('eight-hold controller input schedule changed')
    captures = {}
    for pc in CLOCK_SITES:
        rows = capture(trace, pc)
        if len(rows) != len(offered):
            raise ValueError(f'{pc:03X}: wrong capture cadence')
        codes = [row['latch_q'] for row in rows]
        captures[f'{pc:03X}'] = dict(captures=len(codes),
                                     first_24_codes=codes[:24],
                                     steady_codes=sorted(set(codes[1:])),
                                     photo_b5_values=sorted({photo_b5(v) for v in codes[1:]}),
                                     transitions=sum(a != b for a, b in zip(codes, codes[1:])),
                                     codes=codes)
    # The constant-symbol controls test for any autonomous phase progression
    # at *all* ALU words in the recurring loop, not just at chosen latch sites.
    start = inputs[1]['cycle']
    blocks = [tuple((row['pc'], row['alu']['y']) for row in trace[start + LOOP_WORDS * i:
                                                               start + LOOP_WORDS * (i + 1)])
              for i in range(len(offered) - 1)]
    return dict(result=result, captures=captures,
                distinct_full_loop_blocks=len(set(blocks)),
                first_full_loop_block=[dict(pc=f'{pc:03X}', y=y) for pc, y in blocks[0]])


def run(out=HERE / 'results/split-dac-clock-screen.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    mapping = mapping_for('b')
    _, bits = controller_stream()
    cases = {}
    for label, stream in (('zero', [0] * len(bits)),
                          ('one', [1] * len(bits)), ('actual', bits)):
        cases[label] = trial(mapping, scenario, stream)
    report_cases = {}
    for label, case in cases.items():
        report_cases[label] = dict(trace_digest=case['result']['trace_digest'],
                                   clean=case['result']['clean'],
                                   input_visits=case['result']['address_counts'].get(0x38E, 0),
                                   distinct_full_loop_blocks=case['distinct_full_loop_blocks'],
                                   first_full_loop_block=case['first_full_loop_block'],
                                   clocks={site: {k: v for k, v in clock.items()
                                                  if k != 'codes'}
                                           for site, clock in case['captures'].items()})
    for label in ('zero', 'one'):
        if cases[label]['distinct_full_loop_blocks'] != 1:
            raise ValueError(f'{label}: unexpected autonomous loop progression')
    if (cases['zero']['captures']['39E']['steady_codes'] != [27] or
            cases['one']['captures']['39E']['steady_codes'] != [59] or
            cases['zero']['captures']['38E']['steady_codes'] != [251] or
            cases['one']['captures']['38E']['steady_codes'] != [235]):
        raise ValueError('candidate latch codes changed')
    report = dict(status='hypothetical LS273 clock screen, not physical DAC output',
                  fixture=dict(mapping=mapping['name'], controller_bits=len(bits),
                               controller_bits_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                               samples_per_bit=SAMPLES_PER_BIT,
                               complete_loop_blocks_after_startup=1023,
                               input_byte='00 or 10, controller bit on D4',
                               clock_sites=[f'{pc:03X}' for pc in CLOCK_SITES],
                               latch_data='ALU Y directly to LS273 D1..D8 (untraced)',
                               photo_dac_bit='DAC08 B5 <- LS273 Q4 candidate; Y bit 4 to D4 assumed'),
                  cases=report_cases,
                  limitations=[
                      'Both LS273 clock sites and Y-to-latch data order are untraced hypotheses.',
                      'The D4 bus lane and upper-slice A/B/instruction fields are hypotheses.',
                      'The eight-hold input schedule is a 9600-sample/s versus 1200-bit/s candidate, not a measured board clock.',
                      'The bitstream is a local 8031 scrambler run, not a complete modem command frame.',
                      'This digital replay does not model analog DAC current, filter or line output.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), HERE / 'dac08_latch_probe.py',
                                           HERE / 'independent_slice_addresses.py',
                                           HERE / 'controller_bit_dispatch.py',
                                           HERE / 'photo_controller_path.py',
                                           HERE / 'split_slice_probe.py',
                                           ASSUMED / 'execute.py', HERE.parent / 'model.py')})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for label, case in report['cases'].items():
        print(label, 'loop patterns', case['distinct_full_loop_blocks'],
              {site: (row['steady_codes'], row['photo_b5_values'], row['transitions'])
               for site, row in case['clocks'].items()})
