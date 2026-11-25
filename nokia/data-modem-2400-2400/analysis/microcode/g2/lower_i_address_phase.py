"""Test a same-net per-word phase that lets the 3F7 ROM value reach control."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from split_slice_probe import split_scenario

ROM_PC = 0x3F7
READ_PCS = (0x3F9, 0x3FA)
CYCLES = 512
PULSE_VISIT = 20


def policy(value):
    return dict(value=value, status='hypothesis', evidence=(
        'Diagnostic E4/E2 phase at the reached microinstruction; the latch '
        'clock, phase and physical continuation are untraced'))


def run_case(mapping, base, phase, bank, replay=None):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    scenario['name'] += f'; {phase} address/instruction phase diagnostic'
    if phase in ('address_pc', 'coherent_pc'):
        scenario['inputs']['register_address_bit_overrides_by_pc'] = {
            str(pc): {'a': {'0': policy(0), '1': policy(1)}}
            for pc in READ_PCS}
    if phase == 'coherent_pc':
        scenario['inputs']['instruction_bit_overrides_by_pc'] = {
            str(pc): {'7': policy(0), '0': policy(1)}
            for pc in READ_PCS}
    if phase == 'coherent_global':
        for bit, value in (('0', 0), ('1', 1)):
            scenario['inputs']['register_address_bit_overrides']['a'][bit] = policy(value)
        for bit, value in (('7', 0), ('0', 1)):
            scenario['inputs']['instruction_bit_overrides'][bit] = policy(value)
    if bank == 0:
        scenario['io']['read']['address']['bank_by_pc'] = {str(ROM_PC): 0}
        scenario['io']['read']['address']['evidence'] += (
            '; diagnostic A8=0 at 3F7; bank driver untraced')
    if replay is not None:
        scenario['io']['read']['address']['pcs'].remove(ROM_PC)
        scenario['io']['read']['pc_sequences'][str(ROM_PC)] = replay
        scenario['io']['read']['evidence'] += (
            '; explicit diagnostic 3F7 byte replay; source and timing untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('phase candidate execution incomplete')
    return dict(result=result, trace=trace)


def first_difference(left, right):
    return next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), None)


def classify(run):
    trace = run['trace']
    reads = [row for row in trace if row['pc'] == ROM_PC and
             row['external_read'].get('selected_by_alu')]
    return dict(selected_3f7=len(reads),
                rom_addresses_first_22=[row['external_read'].get('address')
                                        for row in reads[:22]],
                rom_values_first_22=[row['external_read']['value']
                                     for row in reads[:22]],
                visits_3ee=sum(row['pc'] == 0x3EE for row in trace),
                a_3f9=sorted({row['register_address_a'] for row in trace
                              if row['pc'] == 0x3F9}),
                i_3f9=sorted({row['instruction_i'] for row in trace
                              if row['pc'] == 0x3F9}),
                y_distinct_by_site={f'{pc:03X}': sorted({row['alu']['y'] for row in trace
                                                       if row['pc'] == pc})
                                    for pc in (0x3F8, 0x3F9, 0x3FA)},
                final_pc=f"{run['result']['final_state']['pc']:03X}",
                trace_digest=run['result']['trace_digest'])


def run(out=HERE/'results/lower-i-address-phase.json'):
    _, base = fixture()
    mapping = mapping_with_source(6, 0)
    cases = []
    runs = {}
    for phase in ('baseline', 'address_pc', 'coherent_pc', 'coherent_global'):
        pair = {bank: run_case(mapping, base, phase, bank) for bank in (256, 0)}
        runs[phase] = pair
        high, low = pair[256], pair[0]
        cases.append(dict(phase=phase, high=classify(high), low=classify(low),
                          first_pc_divergence=first_difference(
                              [row['pc'] for row in high['trace']],
                              [row['pc'] for row in low['trace']]),
                          first_y_divergence=first_difference(
                              [row['alu']['y'] for row in high['trace']],
                              [row['alu']['y'] for row in low['trace']])))
    by_phase = {row['phase']: row for row in cases}
    baseline = by_phase['baseline']
    address = by_phase['address_pc']
    coherent = by_phase['coherent_pc']
    global_case = by_phase['coherent_global']
    if (baseline['high']['selected_3f7'] != 59 or
            baseline['low']['selected_3f7'] != 59 or
            baseline['first_pc_divergence'] is not None or
            baseline['first_y_divergence'] is not None or
            (address['high']['selected_3f7'], address['low']['selected_3f7']) != (4,59) or
            address['first_pc_divergence'] != 75 or
            (coherent['high']['selected_3f7'], coherent['low']['selected_3f7']) != (59,10) or
            coherent['first_pc_divergence'] != 123 or
            coherent['high']['a_3f9'] != [10] or
            coherent['high']['i_3f9'] != [21] or
            global_case['high']['selected_3f7'] != 0 or
            global_case['low']['selected_3f7'] != 0):
        raise ValueError('address/instruction phase classification changed')
    upper = runs['coherent_pc'][256]
    selected = [row for row in upper['trace'] if row['pc'] == ROM_PC]
    values = [row['external_read']['value'] for row in selected]
    replay = run_case(mapping, base, 'coherent_pc', 256, values)
    if replay['result']['trace_digest'] != upper['result']['trace_digest']:
        raise ValueError('3F7 byte replay did not reproduce the ROM run')
    rom = (HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin').read_bytes()
    original_address = selected[PULSE_VISIT]['external_read']['address']
    alternate_byte = rom[original_address - 256]
    changed = values[:]
    changed[PULSE_VISIT] = alternate_byte
    impulse = run_case(mapping, base, 'coherent_pc', 256, changed)
    first_pc = first_difference([row['pc'] for row in replay['trace']],
                                [row['pc'] for row in impulse['trace']])
    first_y = first_difference([row['alu']['y'] for row in replay['trace']],
                               [row['alu']['y'] for row in impulse['trace']])
    if (original_address != 279 or values[PULSE_VISIT] != 68 or
            alternate_byte != 51 or first_y != 208 or first_pc != 211 or
            replay['trace'][210]['next_pc'] != 0x3EA or
            impulse['trace'][210]['next_pc'] != 0x3EE or
            impulse['result']['address_counts'].get(ROM_PC, 0) != 21):
        raise ValueError('isolated 3F7 byte-to-branch result changed')
    paths = [Path(__file__), HERE/'lower_i_input_pipeline.py',
             HERE/'independent_slice_addresses.py', HERE/'independent_slice_fields.py',
             HERE/'split_slice_probe.py', HERE/'photo_controller_path.py',
             HERE.parent/'assumed/execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='diagnostic same-net address/instruction phase exposes ROM-to-branch path',
                  fixture=dict(lower_i6_source='11.0', cycles=CYCLES, q=5,
                               initial_ram=[0]*16,
                               per_word_phase='E4/E2 levels 0/1 at 3F9 and 3FA only'),
                  cases=cases,
                  isolated_byte=dict(visit=PULSE_VISIT, rom_address=original_address,
                                     original_byte=values[PULSE_VISIT],
                                     alternate_byte=alternate_byte,
                                     replay_matches_rom=True,
                                     first_y_divergence=first_y,
                                     first_pc_divergence=first_pc,
                                     branch_cycle=210, original_next_pc='3EA',
                                     changed_next_pc='3EE',
                                     changed_3f7_visits=21,
                                     trace_digests=dict(replay=replay['result']['trace_digest'],
                                                        impulse=impulse['result']['trace_digest'])),
                  limitations=[
                      'The per-word E4/E2 levels and latch phases are hypotheses; no physical clock or net is verified.',
                      'The route does not receive the controller bitstream or reach a traced DAC output.',
                      'A bank-sensitive branch is not proof that the ROM loop generates the line carrier.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for row in result['cases']:
        print(row['phase'], row['high']['selected_3f7'],
              row['low']['selected_3f7'], row['first_pc_divergence'])
    print(result['isolated_byte'])
