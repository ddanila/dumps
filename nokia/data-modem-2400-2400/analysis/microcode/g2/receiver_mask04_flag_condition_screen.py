"""Check alternative mask-04 TEST flag sources for ADC-dependent branches."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import CYCLES, PATTERNS, configured

SOURCES = ('zero', 'sign', 'carry', 'overflow')
TIMINGS = ('previous', 'current')
CONDITIONAL_COMMANDS = (0, 2, 4, 6)
SURVIVORS = (('previous', 'sign', 1),
             ('previous', 'carry', 1),
             ('previous', 'overflow', 1))


def values_for(pattern):
    samples = codes(pattern, 32, 'complementary')
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != 1500:
        raise ValueError('ADC schedule changed')
    return values


def counts(result):
    return dict(clean=result['clean'],
                cycles=result['completed_cycles'],
                adc_visits=result['address_counts'].get(0x3F8, 0),
                fourth_row_visits=result['address_counts'].get(0x3FE, 0),
                final_pc=f'{result["final_state"]["pc"]:03X}',
                trace_digest=result['trace_digest'])


def held_sweep(mapping, base):
    cases = []
    for timing in TIMINGS:
        for source in SOURCES:
            for polarity in (0, 1):
                result = execute(mapping, configured(base, [9] * 1500,
                                                     timing, source, polarity),
                                 CYCLES, mode='integrated', trace_limit=0)
                cases.append(dict(timing=timing, source=source,
                                  polarity=polarity, **counts(result)))
    survivors = tuple((row['timing'], row['source'], row['polarity'])
                      for row in cases if row['adc_visits'] == 1500 and
                      row['fourth_row_visits'] == 1500)
    if survivors != SURVIVORS:
        raise ValueError(('mask-04 held TEST survivors changed', survivors))
    return cases


def capture(mapping, base, source, pattern):
    scenario = configured(base, values_for(pattern), 'previous', source, 1)
    ram = scenario['initial']['ram'][:]
    q = scenario['initial']['q']
    pc_digest = hashlib.sha256()
    tests = {0x3EA: [], 0x3EC: [], 0x3ED: []}
    conditional = {}
    after_fourth = []
    commands = Counter()
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        summary = counts(result)
        if (not summary['clean'] or summary['cycles'] != CYCLES or
                summary['adc_visits'] != 1500 or
                summary['fourth_row_visits'] != 1500):
            raise ValueError(('mask-04 waveform did not sustain', source,
                              pattern, summary))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            commands[(pc, row['command'])] += 1
            if pc in tests:
                tests[pc].append(row['test'])
            if row['command'] in CONDITIONAL_COMMANDS:
                conditional.setdefault(pc, []).append((row['test'],
                                                        row['next_pc']))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            q = row['q']
            if pc == 0x3FE:
                after_fourth.append(bytes(ram) + bytes((q,)))
    if (len(tests[0x3EA]) != 6001 or len(tests[0x3EC]) != 6001 or
            len(tests[0x3ED]) != 6000 or len(after_fourth) != 1500 or
            commands[(0x3EA, 5)] != 6001 or
            commands[(0x3EC, 4)] != 6001 or
            commands[(0x3ED, 2)] != 6000):
        raise ValueError(('wrapper TEST/command counts changed', source))
    return dict(source=source, pattern=list(pattern), **summary,
                pc_digest=pc_digest.hexdigest(),
                wrapper_test_true={f'{pc:03X}': sum(values)
                                   for pc, values in tests.items()},
                conditional_sites={f'{pc:03X}': len(values)
                                   for pc, values in conditional.items()},
                tests=tests, conditional=conditional,
                after_fourth=after_fourth)


def compare(full, zero):
    site_differences = {}
    for pc in full['tests']:
        left, right = full['tests'][pc], zero['tests'][pc]
        if len(left) != len(right):
            raise ValueError(('wrapper site visit count changed', pc))
        site_differences[f'{pc:03X}'] = sum(a != b for a, b in zip(left, right))
    conditional_differences = {}
    for pc in full['conditional']:
        left, right = full['conditional'][pc], zero['conditional'].get(pc, [])
        conditional_differences[f'{pc:03X}'] = dict(
            full_visits=len(left), zero_visits=len(right),
            test_differences=(sum(a[0] != b[0] for a, b in zip(left, right))
                              if len(left) == len(right) else None),
            next_pc_differences=(sum(a[1] != b[1] for a, b in zip(left, right))
                                 if len(left) == len(right) else None))
    same_pc = full['pc_digest'] == zero['pc_digest']
    total_conditional_test = sum(
        row['test_differences'] for row in conditional_differences.values())
    total_conditional_pc = sum(
        row['next_pc_differences'] for row in conditional_differences.values())
    state_differences = sum(a != b for a, b in
                            zip(full['after_fourth'], zero['after_fourth']))
    if (not same_pc or total_conditional_test or total_conditional_pc or
            state_differences != 1312 or
            site_differences['3EC'] or site_differences['3ED']):
        raise ValueError(('mask-04 conditional branch comparison changed',
                          full['source']))
    return dict(source=full['source'], same_pc_path=same_pc,
                wrapper_test_differences=site_differences,
                conditional_test_differences=total_conditional_test,
                conditional_next_pc_differences=total_conditional_pc,
                conditional_differences=conditional_differences,
                after_fourth_state_differences=state_differences,
                trace_digests=[full['trace_digest'], zero['trace_digest']])


def run(out=HERE / 'results/receiver-mask04-flag-condition-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    held = held_sweep(mapping, base)
    pairs = []
    for _, source, _ in SURVIVORS:
        full = capture(mapping, base, source, PATTERNS[0])
        zero = capture(mapping, base, source, PATTERNS[1])
        pairs.append(compare(full, zero))
        print('compared TEST source', source, flush=True)
    paths = [Path(__file__), HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='mask-04 receive TEST flag alternatives and executed branch audit',
        fixture=dict(mapping='joint upper-source mask 04',
                     dispatch='scenario [0,1,2,3]',
                     held_adc='09 at 3F8, 1500 visits',
                     waveform='paired 32-sample complementary ADC streams',
                     TEST='zero/sign/carry/overflow, previous/current, both polarities',
                     conditional_commands=CONDITIONAL_COMMANDS),
        held_sweep=held, survivors=SURVIVORS, waveform_pairs=pairs,
        limitations=[
            'TEST source, polarity and timing are scenario hypotheses, not traced Nokia pins.',
            'The paired waveforms do not exhaust ADC stimuli or alternative field maps.',
            'No executed branch decision alone would prove a USART RxD route.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('survivors', result['survivors'])
    print('paired results', [
        {key: row[key] for key in
         ('source', 'wrapper_test_differences',
          'conditional_test_differences',
          'after_fourth_state_differences')}
        for row in result['waveform_pairs']])
