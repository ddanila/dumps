"""Find every executed effect of sustained high-RAM return beyond 3FA."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_external_ram_echo_screen as echo
import joint_mask04_ram_pulse_freeze as pulse
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

FIELDS = ('alu', 'q', 'registers', 'test', 'external_read')


def fixtures():
    short_samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if short_samples[25] != 0x51:
        raise ValueError('short waveform changed')
    short_adc = impulse.held_samples(short_samples, 25, None)
    mixed = echo.training_inputs()['remote_plus_echo'] + [0] * echo.TAIL_SAMPLES
    long_adc = [value for index, value in enumerate([127 - x for x in mixed])
                for _ in range(47 if index % 8 < 7 else 46)]
    if len(long_adc) != echo.VISITS:
        raise ValueError('long waveform schedule changed')
    return (
        ('varying_64', short_adc, pulse.sample_starts(),
         pulse.TRAIN_WRITES, impulse.CYCLES, impulse.ADC_VISITS),
        ('mixed_192', long_adc, echo.sample_starts(),
         4 * echo.TRAIN_VISITS, echo.CYCLES, echo.VISITS),
    )


def paired_case(execute, mapping, base, name, adc, starts, writes, cycles, visits,
                read_pc=0x3FA):
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        results = []
        initial = None
        for feedback in (False, True):
            scenario = configured(base, adc, 'previous', 'carry', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True, external_ram_lane='high',
                            external_ram_latch_pc=0x3F9,
                            external_ram_read_pc=read_pc,
                            external_ram_read_offset=-3,
                            external_ram_write_until=writes,
                            external_ram_address_tick_visits=[4 * tick for tick in starts])
            if initial is None:
                initial = scenario['initial']['ram'][:]
            path = Path(tmp) / ('feedback' if feedback else 'write_only')
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=path, trace_limit=cycles)
            if (not result['clean'] or result['completed_cycles'] != cycles or
                    result['address_counts'].get(0x3F8, 0) != visits or
                    result['edge_counts'].get('3ed->3ee', 0)):
                raise ValueError(('receive loop did not sustain', name, feedback))
            paths.append(path / 'trace.jsonl')
            results.append(result)
        counts = {field: Counter() for field in FIELDS}
        first = {}
        ram = [initial[:], initial[:]]
        ram_difference_cycles = [0] * 16
        r13_span_start = None
        r13_span_lengths = Counter()
        r13_rejoin_pcs = Counter()
        r13_first_spans = []
        pc_digest = hashlib.sha256()
        with paths[0].open() as left, paths[1].open() as right:
            for a_line, b_line in zip(left, right):
                a, b = json.loads(a_line), json.loads(b_line)
                if a['cycle'] != b['cycle'] or a['pc'] != b['pc']:
                    raise ValueError(('PC path diverged', name,
                                      a['cycle'], a['pc'], b['pc']))
                cycle = a['cycle']
                pc = f"{a['pc']:03X}"
                pc_digest.update(a['pc'].to_bytes(2, 'little'))
                for field in FIELDS:
                    if a[field] != b[field]:
                        counts[field][pc] += 1
                        first.setdefault(field, dict(cycle=cycle, pc=pc))
                for index, row in enumerate((a, b)):
                    for address, value in row['registers'].items():
                        ram[index][int(address)] = value
                for register in range(16):
                    ram_difference_cycles[register] += (
                        ram[0][register] != ram[1][register])
                if ram[0][13] != ram[1][13]:
                    if r13_span_start is None:
                        r13_span_start = cycle
                elif r13_span_start is not None:
                    length = cycle - r13_span_start
                    r13_span_lengths[length] += 1
                    r13_rejoin_pcs[pc] += 1
                    if len(r13_first_spans) < 5:
                        r13_first_spans.append(dict(first=r13_span_start,
                                                    last=cycle - 1,
                                                    length=length,
                                                    rejoin_pc=pc))
                    r13_span_start = None
        if r13_span_start is not None:
            length = cycles - r13_span_start
            r13_span_lengths[length] += 1
            if len(r13_first_spans) < 5:
                r13_first_spans.append(dict(first=r13_span_start,
                                            last=cycles - 1, length=length))
        if sum(pc_count for pc_count in counts['alu'].values()) == 0:
            raise ValueError(('feedback has no executed ALU effect', name))
        return dict(name=name, adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                    cycles=cycles, visits=visits,
                    trace_digests=[result['trace_digest'] for result in results],
                    pc_digest=pc_digest.hexdigest(),
                    differences={field: dict(by_pc=dict(sorted(counter.items())),
                                             total=sum(counter.values()),
                                             first=first.get(field))
                                 for field, counter in counts.items()},
                    ram_difference_cycles=ram_difference_cycles,
                    r13_span_lengths={str(length): count
                                      for length, count in sorted(r13_span_lengths.items())},
                    r13_rejoin_pcs=dict(sorted(r13_rejoin_pcs.items())),
                    r13_first_spans=r13_first_spans,
                    final_internal_ram_equal=ram[0] == ram[1],
                    final_q_equal=results[0]['final_state']['q'] ==
                                  results[1]['final_state']['q'])


def run(out=HERE / 'results/joint-mask04-ram-carry-propagation.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = [paired_case(execute, mapping, base, *args) for args in fixtures()]
    report = dict(experiment='full-word propagation of previous-carry high-RAM feedback',
                  fixture=dict(condition='previous carry, polarity 1',
                               route='3F9 Y high nibble -> sample-paced RAM -> -3 sample 3FA D high nibble',
                               control='same writes and address clock without readback'),
                  cases=cases,
                  limitations=[
                      'The RAM, TEST mux and output-latch wiring are assumed.',
                      'A difference confined to 3FA and R13 under these two inputs does not prove all modes lack feedback propagation.',
                      'No analog line residual or received bit is identified.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
