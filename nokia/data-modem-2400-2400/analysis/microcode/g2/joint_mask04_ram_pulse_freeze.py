"""Test whether an assumed external RAM returns a one-sample ADC pulse after freeze."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

TRAIN_SAMPLES = impulse.VARYING_PULSE_SAMPLE + 1
TRAIN_VISITS = sum(47 if sample % 8 < 7 else 46
                   for sample in range(TRAIN_SAMPLES))
TRAIN_WRITES = 4 * TRAIN_VISITS
ROUTES = (
    ('write_only', False, True, -16),
    ('read_3', True, True, -3),
    ('read_16', True, True, -16),
    ('read_16_no_writes', True, False, -16),
)


def sample_starts():
    starts = []
    visit = 0
    for sample in range(impulse.SAMPLES):
        starts.append(visit)
        visit += 47 if sample % 8 < 7 else 46
    if visit != impulse.ADC_VISITS or starts[TRAIN_SAMPLES] != TRAIN_VISITS:
        raise ValueError('sample schedule changed')
    return starts


def delta(left, right, start, stop):
    changed = [i for i in range(start, stop) if left[i] != right[i]]
    return dict(count=len(changed), first=changed[0] if changed else None,
                last=changed[-1] if changed else None,
                first_values=([left[changed[0]], right[changed[0]]]
                              if changed else None))


def run(out=HERE / 'results/joint-mask04-ram-pulse-freeze.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if len(samples) != impulse.SAMPLES or samples[25] != 0x51:
        raise ValueError('reference samples changed')
    starts = sample_starts()
    offered = dict(baseline=impulse.held_samples(samples, 25, None),
                   pulse=impulse.held_samples(samples, 25,
                                              impulse.VARYING_HIGH_PULSE_ADC))
    cases = []
    observed = {}
    memory = {}
    for input_name, adc in offered.items():
        for route, feedback, write, lag in ROUTES:
            scenario = configured(base, adc, 'previous', 'overflow', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=write,
                            external_ram_lane='low',
                            external_ram_latch_pc=0x3F9,
                            external_ram_read_pc=0x3FA,
                            external_ram_read_offset=lag,
                            external_ram_write_until=TRAIN_WRITES,
                            external_ram_address_tick_visits=[4 * visit for visit in starts])
            result = execute(mapping, scenario, impulse.CYCLES,
                             mode='integrated', trace_limit=0)
            ram = result['external_ram_candidate']
            y = ram['y_by_pc']
            if (not result['clean'] or result['completed_cycles'] != impulse.CYCLES
                    or result['read_sequence_visits'].get(0x3F8) != impulse.ADC_VISITS
                    or result['edge_counts'].get('3ed->3ee', 0) != 0
                    or any(len(y[pc]) != impulse.ADC_VISITS
                           for pc in (0x3F8, 0x3F9, 0x3FA))
                    or ram['writes'] != (TRAIN_WRITES if write else 0)):
                raise ValueError(('receive loop did not sustain', input_name, route))
            observed[(input_name, route)] = y
            memory[(input_name, route)] = ram['bytes']
            cases.append(dict(input=input_name, route=route,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              completed_cycles=result['completed_cycles'],
                              loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                              trace_digest=result['trace_digest'],
                              external_reads=ram['reads'],
                              external_writes=ram['writes'],
                              noninitial_ram_bytes=sum(x != 1 for x in ram['bytes']),
                              ram_sha256=hashlib.sha256(bytes(ram['bytes'])).hexdigest(),
                              first_noninitial_read=ram['first_changed_read']))
            print(input_name, route, result['trace_digest'], flush=True)
    windows = dict(pulse=(starts[25], starts[26]),
                   frozen_before_3=(starts[26], starts[28]),
                   delayed_3=(starts[28], starts[29]),
                   frozen_before_16=(starts[26], starts[41]),
                   delayed_16=(starts[41], starts[42]),
                   entire_frozen_tail=(starts[26], impulse.ADC_VISITS))
    comparisons = {}
    for route, _, _, _ in ROUTES:
        a = observed[('baseline', route)]
        b = observed[('pulse', route)]
        comparisons[route] = dict(
            changed_ram_bytes=[dict(address=i, baseline=pair[0], pulse=pair[1])
                               for i, pair in enumerate(zip(
                                   memory[('baseline', route)], memory[('pulse', route)]))
                               if pair[0] != pair[1]],
            y_by_window={f'{pc:03X}': {
                name: delta(a[pc], b[pc], *bounds)
                for name, bounds in windows.items()}
                for pc in (0x3F8, 0x3F9, 0x3FA)})
    report = dict(
        experiment='one-sample ADC pulse in sample-paced candidate RAM, frozen immediately afterward',
        fixture=dict(dibits=impulse.VARYING_DIBITS, samples=impulse.SAMPLES,
                     pulse_sample=25, baseline_adc=0x51, pulse_adc=0xB1,
                     train_samples=TRAIN_SAMPLES, train_visits=TRAIN_VISITS,
                     train_writes=TRAIN_WRITES,
                     adc_visits=impulse.ADC_VISITS, cycles=impulse.CYCLES,
                     routes=ROUTES, windows=windows,
                     candidate_ram='256x8 initial 01; 3F9 Y low nibble latched; 3EC write; 3FA D low-nibble return with D0 forced 1; one address tick per ADC sample, four 3EA visits per ADC visit'),
        cases=cases, comparisons=comparisons,
        limitations=[
            'RAM pin route, address clock, write gate, read lag and return lane are explicit assumptions.',
            'A delayed Y change through modeled RAM is not an echo residual or a received bit.',
            'A single reference waveform and pulse cannot establish general receive or echo behavior.'
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (Path(__file__), Path(impulse.__file__),
                                    HERE / 'joint_upper_ram_feedback_screen.py',
                                    HERE.parent / 'assumed/execute.py',
                                    HERE / 'receiver_four_row_condition_screen.py',
                                    HERE / 'reference_modem.py', MAPPINGS['q3'],
                                    *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
