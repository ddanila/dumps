"""Test whether one ADC high-nibble change persists in the joint map."""

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
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

VISITS = 6000
CONTROL_BYTE = 0x09
PULSE_BYTE = 0x59
PULSE_VISITS = (10, 11, 12, 13, 14, 100, 101, 102, 103, 104)
CYCLES = 8 * VISITS + 47


def trace(mapping, base, pulse_visit=None):
    values = [CONTROL_BYTE] * VISITS
    if pulse_visit is not None:
        values[pulse_visit] = PULSE_BYTE
    scenario = scenario_for_full_byte(base, values, 'complementary')
    ram = scenario['initial']['ram'][:]
    pc_digest = hashlib.sha256()
    rows, addresses = [], []
    observed_input = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(bytes((pc & 255, pc >> 8)))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc == 0x3F8:
                event = row['external_read']
                if not event.get('selected_by_alu'):
                    raise ValueError('D3F8 ADC byte was not selected')
                observed_input.append(event['value'])
            elif pc == 0x3F9:
                addresses.append(row['external_read']['address'])
            elif pc == 0x3FA:
                rows.append((bytes(ram), row['q'], row['alu']['y']))
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            len(rows) != VISITS or len(addresses) != VISITS or
            observed_input != values):
        raise ValueError(('pulse-memory run incomplete', pulse_visit))
    return dict(rows=rows, addresses=addresses,
                pc_digest=pc_digest.hexdigest(),
                trace_digest=result['trace_digest'])


def compare(control, trial, pulse_visit):
    if control['pc_digest'] != trial['pc_digest']:
        raise ValueError(('pulse changed PC path', pulse_visit))
    states = control['rows'], trial['rows']
    changed_state = [i for i, (a, b) in enumerate(zip(*states)) if a != b]
    changed_address = [i for i, (a, b) in enumerate(zip(
        control['addresses'], trial['addresses'])) if a != b]
    if (not changed_state or not changed_address or
            changed_state[0] != pulse_visit or
            changed_address[0] != pulse_visit):
        raise ValueError(('pulse had no immediate state/address response',
                          pulse_visit))
    register_counts = {f'R{register}': count for register in range(16)
                       if (count := sum(a[0][register] != b[0][register]
                                        for a, b in zip(*states)))}
    delta = [(b - a) & 255 for a, b in zip(
        control['addresses'][pulse_visit + 1:],
        trial['addresses'][pulse_visit + 1:])]
    steady = delta[-500:]
    return dict(pulse_visit=pulse_visit, pulse_byte=f'{PULSE_BYTE:02X}',
                common_byte=f'{CONTROL_BYTE:02X}',
                same_pc_path=True,
                state_differences=len(changed_state),
                later_state_differences=sum(i > pulse_visit for i in changed_state),
                last_state_difference=changed_state[-1],
                state_difference_persists_to_end=(changed_state[-1] == VISITS - 1),
                next_rom_address_differences=len(changed_address),
                later_rom_address_differences=sum(i > pulse_visit for i in changed_address),
                last_rom_address_difference=changed_address[-1],
                rom_address_difference_persists_to_end=(changed_address[-1] == VISITS - 1),
                register_difference_visits=register_counts,
                q_difference_visits=sum(a[1] != b[1] for a, b in zip(*states)),
                y3fa_difference_visits=sum(a[2] != b[2] for a, b in zip(*states)),
                first_12_later_rom_address_deltas=delta[:12],
                last_10_rom_address_deltas=delta[-10:],
                last_500_rom_address_delta_histogram=dict(sorted(Counter(steady).items())),
                trace_digest=trial['trace_digest'])


def run(out=HERE / 'results/joint-upper-adc-pulse-memory.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    mapping = candidate(receiver, transmitter, SELECTED_MASK)
    _, base = fixture()
    control = trace(mapping, base)
    cases = [compare(control, trace(mapping, base, visit), visit)
             for visit in PULSE_VISITS]
    for early, late in zip(cases[:5], cases[5:]):
        if (late['pulse_visit'] - early['pulse_visit'] != 90 or
                late['state_difference_persists_to_end'] !=
                early['state_difference_persists_to_end'] or
                late['rom_address_difference_persists_to_end'] !=
                early['rom_address_difference_persists_to_end'] or
                (early['later_state_differences'] -
                 late['later_state_differences']) not in (0, 90)):
            raise ValueError('five-visit pulse phase response did not repeat')
    phase_classes = [dict(visit_mod_5=case['pulse_visit'] % 5,
                          state_persists=case['state_difference_persists_to_end'],
                          rom_address_persists=case['rom_address_difference_persists_to_end'],
                          later_different_visits=case['later_state_differences'])
                     for case in cases[:5]]
    paths = [Path(__file__), HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='single ADC high-nibble change persists in modeled joint-map Q/RAM and ROM feedback',
                  fixture=dict(mapping='joint upper-source mask 08',
                               initial_q=5, initial_ram=[0] * 16,
                               control_byte=f'{CONTROL_BYTE:02X}',
                               one_visit_pulse_byte=f'{PULSE_BYTE:02X}',
                               pulse_visits=list(PULSE_VISITS),
                               compared_visits=VISITS,
                               subsequent_input='identical control byte for every later visit',
                               high_instruction_at_d3f8='D5',
                               sample_clock='one offered byte per D3F8 visit; diagnostic, not physical conversion schedule'),
                  control_trace_digest=control['trace_digest'],
                  cases=cases, phase_classes=phase_classes,
                  limitations=[
                      'A lasting state difference is memory, not a dibit decision, receive output or echo-canceller proof.',
                      'The one-visit pulse is diagnostic; the photographed ADC conversion clock and bus are untraced.',
                      'Upper instruction wiring, register-address levels and condition source remain hypothetical.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(case['pulse_visit'], case['later_state_differences'],
            case['later_rom_address_differences']) for case in report['cases']])
