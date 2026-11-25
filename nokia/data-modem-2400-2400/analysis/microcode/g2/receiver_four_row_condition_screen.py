"""Screen 3ED condition choices for a counter-like four-row receive dispatch."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_3eb_adc_route_screen import CYCLES, scenario

ROW_STARTS = (0x3EF, 0x3F3, 0x3F7, 0x3FB)
ROW_PCS = tuple(pc for start in ROW_STARTS for pc in range(start, start + 4))
ROW_ENDS = tuple(start + 3 for start in ROW_STARTS)
PCS = (0x3EA, 0x3EB, 0x3EC, 0x3ED) + ROW_PCS
FIELDS = ('test', 'next_pc', 'q', 'alu.y', 'alu.sign', 'alu.zero',
          'alu.carry', 'alu.overflow')
ADC_VISITS = 1500
PATTERNS = ((0, 1, 3, 2), (0, 0, 0, 0))


def configured(base, values, timing, source, polarity):
    candidate = scenario(base, False, True, values)
    candidate['dispatch']['sequence'] = [0, 1, 2, 3]
    candidate['condition']['sources'][0] = source
    candidate['condition']['polarity'][0] = polarity
    candidate['condition']['flag_timing'] = timing
    candidate['condition']['evidence'] = (
        'diagnostic counter-like four-row dispatch and select-0 ALU flag; '
        'TEST pin source, polarity and timing untraced')
    return candidate


def counts(result):
    reached = result['address_counts']
    return dict(adc_visits=reached.get(0x3F8, 0),
                selected_adc_reads=result['read_sequence_visits'].get(0x3F8, 0),
                row_visits=[reached.get(pc, 0) for pc in ROW_STARTS],
                final_pc=f'{result["final_state"]["pc"]:03X}',
                trace_digest=result['trace_digest'])


def sweep(mapping, base):
    cases = []
    for timing in ('previous', 'current'):
        for source in ('zero', 'sign', 'carry', 'overflow'):
            for polarity in (0, 1):
                result = execute(mapping, configured(base, [0x09] * 3000,
                                                     timing, source, polarity),
                                 CYCLES, mode='integrated', trace_limit=0)
                if not result['clean'] or result['completed_cycles'] != CYCLES:
                    raise ValueError('condition sweep did not complete')
                cases.append(dict(timing=timing, source=source,
                                  polarity=polarity, **counts(result)))
    survivors = [(row['timing'], row['source'], row['polarity'])
                 for row in cases if row['adc_visits'] == ADC_VISITS]
    expected = [('previous', 'overflow', 1), ('current', 'zero', 0),
                ('current', 'sign', 1), ('current', 'carry', 1),
                ('current', 'overflow', 1)]
    if survivors != expected or any(row['row_visits'] != [1501, 1500, 1500, 1500]
                                    for row in cases if row['adc_visits'] == ADC_VISITS):
        raise ValueError(('four-row condition survivors changed', survivors))
    return cases


def capture(mapping, base, pattern):
    samples = codes(pattern, 32, 'complementary')
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('four-row ADC hold schedule changed')
    rows = {pc: [] for pc in PCS}
    addresses = {pc: [] for pc in PCS}
    states = {pc: [] for pc in ROW_ENDS}
    pc_digest = hashlib.sha256()
    candidate_scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = list(candidate_scenario['initial']['ram'])
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, candidate_scenario,
                         CYCLES, mode='integrated', out=temporary,
                         trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc in states:
                states[pc].append(bytes(ram) + bytes((row['q'],)))
            if pc not in rows:
                continue
            rows[pc].append(tuple(row['alu'][field[4:]]
                                  if field.startswith('alu.') else row[field]
                                  for field in FIELDS))
            read = row.get('external_read', {})
            if 'address' in read:
                addresses[pc].append(read['address'])
            if pc == 0x3F8 and (not read.get('selected_by_alu') or
                                read['value'] != values[len(rows[pc]) - 1]):
                raise ValueError('four-row ADC byte not selected')
    expected = [6001, 6001, 6001, 6000, 1501] + [1500] * 15
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            counts(result)['adc_visits'] != ADC_VISITS or
            [len(rows[pc]) for pc in PCS] != expected):
        raise ValueError('four-row waveform did not sustain')
    return rows, addresses, states, result, pc_digest.hexdigest(), samples


def compare(left, right):
    a, a_addresses, a_states, a_result, a_pc, a_samples = left
    b, b_addresses, b_states, b_result, b_pc, b_samples = right
    if a_pc != b_pc or a_result['trace_digest'] == b_result['trace_digest']:
        raise ValueError('four-row input contrast or PC path changed')
    sites = {}
    for pc in PCS:
        fields = {}
        for index, field in enumerate(FIELDS):
            differences = [visit for visit, (x, y) in
                           enumerate(zip(a[pc], b[pc])) if x[index] != y[index]]
            fields[field] = dict(differences=len(differences),
                                 first=(differences[0] if differences else None))
        if len(a_addresses[pc]) != len(b_addresses[pc]):
            raise ValueError('ROM read count changed')
        fields['rom_address'] = dict(
            reads=len(a_addresses[pc]),
            differences=sum(x != y for x, y in
                            zip(a_addresses[pc], b_addresses[pc])))
        sites[f'{pc:03X}'] = fields
    state_differences = {}
    for pc in ROW_ENDS:
        if len(a_states[pc]) != len(b_states[pc]):
            raise ValueError('row boundary count changed')
        state_differences[f'{pc:03X}'] = dict(
            visits=len(a_states[pc]),
            any_byte_differences=sum(x != y for x, y in
                                     zip(a_states[pc], b_states[pc])),
            byte_differences=[sum(x[index] != y[index] for x, y in
                                  zip(a_states[pc], b_states[pc]))
                              for index in range(17)])
    return dict(pc_digest=a_pc, streams=[
        dict(pattern=list(pattern),
             first_adc_codes=[f'{code:02X}' for code in samples[:8]],
             trace_digest=result['trace_digest'])
        for pattern, samples, result in
        ((PATTERNS[0], a_samples, a_result),
         (PATTERNS[1], b_samples, b_result))], sites=sites,
                state_differences=state_differences)


def run(out=HERE / 'results/receiver-four-row-condition-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    cases = sweep(mapping, base)
    waveform_cases = []
    for timing, source, polarity in (
            ('previous', 'overflow', 1), ('current', 'zero', 0),
            ('current', 'sign', 1), ('current', 'carry', 1),
            ('current', 'overflow', 1)):
        for pattern in PATTERNS:
            samples = codes(pattern, 32, 'complementary')
            values = [sample for index, sample in enumerate(samples)
                      for _ in range(47 if index % 8 < 7 else 46)]
            result = execute(mapping, configured(base, values, timing,
                                                 source, polarity),
                             CYCLES, mode='integrated', trace_limit=0)
            row = dict(timing=timing, source=source, polarity=polarity,
                       pattern=list(pattern), **counts(result))
            if (not result['clean'] or row['adc_visits'] != ADC_VISITS or
                    row['selected_adc_reads'] != ADC_VISITS or
                    row['row_visits'] != [1501, 1500, 1500, 1500]):
                raise ValueError(('four-row waveform did not sustain', row))
            waveform_cases.append(row)
    contrast = compare(capture(mapping, base, PATTERNS[0]),
                       capture(mapping, base, PATTERNS[1]))
    if (any(site['next_pc']['differences'] for site in contrast['sites'].values()) or
            contrast['sites']['3F9']['rom_address']['differences'] < 100):
        raise ValueError('four-row branch or ROM contrast changed')
    report = dict(
        experiment='four-row receive dispatch under candidate ALU TEST sources',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario [0,1,2,3] at 3EC',
                     condition='select 0 flag source/polarity and timing swept',
                     adc='complementary 127-PCM at 3F8; seven 47-visit and one 46-visit hold per eight samples',
                     cycles=CYCLES, expected_adc_visits=ADC_VISITS),
        held_input_cases=cases, waveform_cases=waveform_cases,
        waveform_contrast=contrast,
        limitations=[
            'The counter-like dispatch, TEST flag wiring, ADC bus and sample clock are hypotheses.',
            'Identical PC paths do not rule out a separately clocked decision or output latch.',
            'Input-dependent table arithmetic is not a recovered dibit or USART RxD event.'],
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for pc, site in report['waveform_contrast']['sites'].items():
        print(pc, {field: data['differences'] for field, data in site.items()})
