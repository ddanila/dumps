"""Release the real receive wrapper after row 2 or 3 and follow its caller."""

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
from receiver_four_row_condition_screen import configured

PATTERNS = ((0, 0, 0, 0), (1, 1, 1, 1), (2, 2, 2, 2),
            (3, 3, 3, 3), (0, 1, 3, 2))
VISITS = 1500
RELEASE_CYCLES = {'after_adc_row': 48034, 'after_fourth_row': 48042}
TAIL_CYCLES = 1024


def run_case(mapping, base, pattern, phase, release):
    samples = codes(pattern, 32, 'complementary')
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != VISITS:
        raise ValueError('four-row ADC hold changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    scenario['condition']['sources'][0] = 'external'
    scenario['condition']['polarity'][0] = 0
    scenario['condition']['evidence'] = (
        'diagnostic timed TEST gate at 3ED; photos do not trace this gate')
    scenario['inputs']['external'] = dict(
        mode='cycle-events', status='hypothesis', initial=1,
        events=[[release, 0]],
        evidence='release 3ED after selected table row; clock and TEST wire untraced')
    ram = scenario['initial']['ram'][:]
    control = hashlib.sha256()
    checkpoints = {}
    first_084 = None
    suffix_words = []
    suffix = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, release + TAIL_CYCLES,
                         mode='integrated', out=temporary,
                         trace_limit=release + 256)
        if (not result['clean'] or
                result['completed_cycles'] != release + TAIL_CYCLES or
                result['address_counts'].get(0x3F8, 0) != VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != VISITS):
            raise ValueError(('timed receive caller did not complete', phase,
                              pattern))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            for address, value in row['registers'].items():
                ram[int(address)] = value
            cycle = row['cycle']
            pc = row['pc']
            if cycle >= release and first_084 is None:
                control.update(pc.to_bytes(2, 'little'))
                control.update(row['next_pc'].to_bytes(2, 'little'))
                control.update(bytes((row['test'],)))
                suffix.append([pc, row['next_pc'], row['test']])
                if len(suffix_words) < 20:
                    suffix_words.append(f'{pc:03X}')
            if cycle == release:
                if pc != 0x3ED or row['next_pc'] != 0x3EE or row['test'] != 0:
                    raise ValueError('TEST release missed 3ED')
                checkpoints['release'] = dict(pc=f'{pc:03X}',
                                              ram=ram[:], q=row['q'])
            if pc == 0x18D and 'caller_entry' not in checkpoints:
                checkpoints['caller_entry'] = dict(cycle=cycle,
                                                   ram=ram[:], q=row['q'])
            if pc == 0x84 and first_084 is None:
                first_084 = cycle
                checkpoints['first_084'] = dict(cycle=cycle,
                                                ram=ram[:], q=row['q'])
    if first_084 is None or set(checkpoints) != {
            'release', 'caller_entry', 'first_084'}:
        raise ValueError('receive caller did not reach terminal word')
    return dict(pattern=list(pattern), phase=phase, release_cycle=release,
                adc_visits=VISITS, first_084_cycle=first_084,
                control_digest_to_084=control.hexdigest(),
                first_suffix_words=suffix_words,
                checkpoints=checkpoints,
                suffix=suffix,
                final_state=result['final_state'],
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/receiver-four-row-caller-handoff.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    cases = []
    for phase, release in RELEASE_CYCLES.items():
        for pattern in PATTERNS:
            cases.append(run_case(mapping, base, pattern, phase, release))
            print('captured', phase, pattern, flush=True)
    summaries = {}
    for phase in RELEASE_CYCLES:
        rows = [case for case in cases if case['phase'] == phase]
        summaries[phase] = dict(
            first_084_cycles=sorted({case['first_084_cycle'] for case in rows}),
            control_digests=len({case['control_digest_to_084'] for case in rows}),
            distinct_pc_paths=len({tuple((pc, next_pc) for pc, next_pc, _ in case['suffix'])
                                   for case in rows}),
            distinct_release_ram_q=len({
                (tuple(case['checkpoints']['release']['ram']),
                 case['checkpoints']['release']['q']) for case in rows}),
            distinct_terminal_ram_q=len({
                (tuple(case['checkpoints']['first_084']['ram']),
                 case['checkpoints']['first_084']['q']) for case in rows}))
        baseline = rows[0]['suffix']
        summaries[phase]['first_differences_from_zero'] = [
            dict(pattern=case['pattern'],
                 difference=next((dict(index=index, zero=left, other=right)
                                  for index, (left, right) in enumerate(
                                      zip(baseline, case['suffix'])) if left != right),
                                 None))
            for case in rows[1:]]
    if (summaries['after_adc_row']['distinct_release_ram_q'] <= 1 or
            summaries['after_fourth_row']['distinct_release_ram_q'] != 1 or
            any(summary['distinct_pc_paths'] != 1 for summary in summaries.values()) or
            summaries['after_fourth_row']['control_digests'] != 1):
        raise ValueError('receive handoff classification changed')
    paths = [Path(__file__), HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='timed receive-table release into actual 18D caller',
        fixture=dict(mapping='joint upper-source mask 08',
                     adc='complementary reference PCM, 47/46 table visits per sample',
                     dispatch='scenario [0,1,2,3]',
                     test='external 1→0 at specified cycle; assumed TEST route',
                     release_cycles=RELEASE_CYCLES,
                     cycles_after_release=TAIL_CYCLES,
                     patterns=PATTERNS),
        cases=cases, summaries=summaries,
        limitations=[
            'Timed select-0 TEST release is a diagnostic input hypothesis, not traced wiring.',
            'Five 32-sample patterns are tested; no USART RxD or DAC output is identified.',
            'Control-path equality does not exclude a separately clocked output latch.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summaries'])
