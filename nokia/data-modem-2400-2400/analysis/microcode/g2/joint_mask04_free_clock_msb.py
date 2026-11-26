"""Test a free-running DAC latch clock at four joint-map transmit phases."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_four_row_retention_tx import (MAPPINGS, candidate, fixture,
                                         hold_candidate, mapped,
                                         mapping_with_upper_source,
                                         split_scenario)
from joint_mask04_dac_msb_data import score
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs

TXREADY = HERE / 'results/main-loop-usart-txready.json'
PRIOR = HERE / 'results/joint-four-row-retention-tx.json'
EDGE = HERE / 'results/joint-mask04-tx-prom-edge.json'
BUSES = HERE / 'results/photo-random-dibit-validation.json'
SITES = (0x127, 0x128, 0x129, 0x12A)
START_CYCLE = 40
CYCLES_PER_SAMPLE = 1500


def site_streams(path):
    streams = {pc: [] for pc in SITES}
    count = TOTAL_SYMBOLS * 8
    with path.open() as source:
        for line in source:
            row = json.loads(line)
            offset = row['cycle'] - START_CYCLE
            if offset < 0 or offset // CYCLES_PER_SAMPLE >= count:
                continue
            phase = offset % CYCLES_PER_SAMPLE
            if phase < 4:
                pc = SITES[phase]
                if row['pc'] != pc:
                    raise ValueError(('free clock left four-word loop', row['cycle'], row['pc']))
                streams[pc].append(row['alu']['y'])
    if any(len(stream) != count for stream in streams.values()):
        raise ValueError(('free clock sample count changed',
                          {f'{pc:03X}': len(stream) for pc, stream in streams.items()}))
    return streams


def replay(mapping, base, tx_case, prior_case, edge_case, buses):
    selector = tx_case['selector']
    symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(tx_case)
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; joint mask04 free-running DAC clock screen'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        streams = site_streams(Path(temporary) / 'trace.jsonl')
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['trace_digest'] != prior_case['trace_digest'] or
            result['trace_digest'] != edge_case['trace_digest']):
        raise ValueError(('joint transmit PROM trace changed', selector))
    if (hashlib.sha256(bytes(streams[0x129])).hexdigest() !=
            edge_case['raw_post_rom_sha256'] or
            hashlib.sha256(bytes(mapped_codes(streams[0x128], SELECTED))).hexdigest() !=
            edge_case['selected_bus_sha256']['pre_rising']):
        raise ValueError(('free-clock capture differs from PROM edge', selector))
    sites = []
    for pc, raw in streams.items():
        rows = []
        for index, bus in enumerate(buses):
            codes = mapped_codes(raw, bus)
            rows.append(dict(bus_index=index,
                             full=score(codes, symbols),
                             msb_only=score([value & 0x80 for value in codes], symbols),
                             lower_seven_only=score([value & 0x7F for value in codes], symbols)))
        sites.append(dict(pc=f'{pc:03X}', samples=len(raw),
                          raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          selected_bus_sha256=hashlib.sha256(
                              bytes(mapped_codes(raw, SELECTED))).hexdigest(),
                          rows=rows))
    return dict(selector=selector, cycles=cycles,
                trace_digest=result['trace_digest'], sites=sites)


def run(out=HERE / 'results/joint-mask04-free-clock-msb.json'):
    txready = json.loads(TXREADY.read_text())
    prior = json.loads(PRIOR.read_text())
    edge = json.loads(EDGE.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6 or any(bus[7] != 7 for bus in buses):
        raise ValueError('surviving DAC buses changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = [replay(mapping, base,
                    next(row for row in txready['cases'] if row['selector'] == selector),
                    next(row for row in prior['transmit_mask04'] if row['selector'] == selector),
                    next(row for row in edge['cases'] if row['selector'] == selector),
                    buses)
             for selector in ('40', '60')]
    summary = {site['pc']: dict(
        full_peak_hz=sorted({row['full']['tone_peak_hz']
                             for case in cases for item in case['sites']
                             if item['pc'] == site['pc'] for row in item['rows']}),
        full_error_range=[min(row['full']['data']['errors']
                              for case in cases for item in case['sites']
                              if item['pc'] == site['pc'] for row in item['rows']),
                          max(row['full']['data']['errors']
                              for case in cases for item in case['sites']
                              if item['pc'] == site['pc'] for row in item['rows'])],
        msb_peak_hz=sorted({row['msb_only']['tone_peak_hz']
                            for case in cases for item in case['sites']
                            if item['pc'] == site['pc'] for row in item['rows']}),
        msb_error_range=[min(row['msb_only']['data']['errors']
                             for case in cases for item in case['sites']
                             if item['pc'] == site['pc'] for row in item['rows']),
                         max(row['msb_only']['data']['errors']
                             for case in cases for item in case['sites']
                             if item['pc'] == site['pc'] for row in item['rows'])])
               for site in cases[0]['sites']}
    paths = [Path(__file__), TXREADY, PRIOR, EDGE, BUSES,
             HERE / 'joint_mask04_dac_msb_data.py',
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='free-running candidate DAC latch phase on fixed joint mask04 transmit map',
                  fixture=dict(mapping='joint upper-source lower mask 04',
                               source='controller-derived call/answer A1-A4 stream',
                               capture='one free-running latch edge per 1500 microinstructions',
                               clock_hypothesis='9600 Hz if one 14.4 MHz oscillator period per microinstruction',
                               analog='assumed 1950 Hz Q=1 bandpass',
                               decoder='external known-carrier reference receiver'),
                  cases=cases, summary=summary,
                  limitations=[
                      'The free-running clock, microinstruction period, Y-to-latch data bus, DAC08 bus, analog filter and physical line route are untraced.',
                      'All six bus orders share Y7-to-DAC MSB, so repeated MSB-only scores are not independent streams.',
                      'A decoder accepting several phases cannot identify the actual latch clock from this test alone.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summary'])
