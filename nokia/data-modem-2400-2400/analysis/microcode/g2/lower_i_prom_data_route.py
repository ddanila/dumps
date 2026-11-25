"""Screen PROM data-bit alternatives for the paired I7/A0 and I0/A1 nets."""

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

CYCLES = 512
ROM_PC = 0x3F7
PULSE_VISIT = 30
SOURCES_I7_A0 = ('!11.2', '!10.6')
SOURCES_I0_A1 = ('11.2', '10.6')


def mapping_for(i7_a0, i0_a1):
    mapping = mapping_with_source(6, 0)
    mapping['name'] += f'-diagnostic-{i7_a0}-{i0_a1}-paired-data-sources'
    mapping['fields']['i']['bits'][7] = i7_a0
    mapping['fields']['i']['bits'][0] = i0_a1
    mapping['fields']['a']['bits'][0] = i7_a0
    mapping['fields']['a']['bits'][1] = i0_a1
    note = (f'; diagnostic paired I7/A0={i7_a0}, I0/A1={i0_a1} PROM data '
            'sources; source-to-latch routes and any inverter are untraced; '
            'U10 E2 low and U11 E4 high are assumed for valid data')
    mapping['fields']['i']['evidence'] += note
    mapping['fields']['a']['evidence'] += note
    return mapping


def run_trace(mapping, base, bank=256, replay=None):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    scenario['name'] += ('; diagnostic paired data-bit route; U10 E2 low, '
                         'U11 E4 high assumed during reads')
    for bit in ('7', '0'):
        scenario['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        scenario['inputs']['register_address_bit_overrides']['a'].pop(bit)
    if bank == 0:
        scenario['io']['read']['address']['bank_by_pc'] = {str(ROM_PC): 0}
        scenario['io']['read']['address']['evidence'] += (
            '; diagnostic A8=0 at 3F7; physical bank source untraced')
    if replay is not None:
        scenario['io']['read']['address']['pcs'].remove(ROM_PC)
        scenario['io']['read']['pc_sequences'][str(ROM_PC)] = replay
        scenario['io']['read']['evidence'] += (
            '; diagnostic 3F7 byte replay; source and timing untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('data-bit route run incomplete')
    return dict(result=result, trace=trace)


def first_difference(left, right):
    return next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), None)


def classify(run):
    trace = run['trace']
    reads = [row for row in trace if row['pc'] == ROM_PC and
             row['external_read'].get('selected_by_alu')]
    return dict(selected_3f7=len(reads),
                first_20_rom_addresses=[row['external_read'].get('address')
                                        for row in reads[:20]],
                first_20_rom_values=[row['external_read']['value']
                                     for row in reads[:20]],
                a_3f9=sorted({row['register_address_a'] for row in trace
                              if row['pc'] == 0x3F9 and 'register_address_a' in row}),
                i_3f9=sorted({row['instruction_i'] for row in trace
                              if row['pc'] == 0x3F9 and 'instruction_i' in row}),
                y_distinct_after_8={f'{pc:03X}': len(set(
                    [row['alu']['y'] for row in trace if row['pc'] == pc][8:]))
                    for pc in (0x3F8, 0x3F9, 0x3FA)},
                final_pc=f"{run['result']['final_state']['pc']:03X}",
                trace_digest=run['result']['trace_digest'])


def run(out=HERE/'results/lower-i-prom-data-route.json'):
    _, base = fixture()
    cases = []
    upper_winner = None
    for i7_a0 in SOURCES_I7_A0:
        for i0_a1 in SOURCES_I0_A1:
            mapping = mapping_for(i7_a0, i0_a1)
            high = run_trace(mapping, base)
            low = run_trace(mapping, base, bank=0)
            cases.append(dict(i7_a0=i7_a0, i0_a1=i0_a1,
                              high=classify(high), low=classify(low),
                              first_pc_divergence=first_difference(
                                  [row['pc'] for row in high['trace']],
                                  [row['pc'] for row in low['trace']]),
                              first_y_divergence=first_difference(
                                  [row['alu']['y'] for row in high['trace']],
                                  [row['alu']['y'] for row in low['trace']])))
            if (i7_a0, i0_a1) == ('!10.6', '11.2'):
                upper_winner = (mapping, high)
    by_pair = {(row['i7_a0'], row['i0_a1']): row for row in cases}
    winner = by_pair[('!10.6', '11.2')]
    if ([(row['i7_a0'], row['i0_a1'], row['high']['selected_3f7'],
          row['low']['selected_3f7']) for row in cases] != [
              ('!11.2', '11.2', 6, 12), ('!11.2', '10.6', 0, 0),
              ('!10.6', '11.2', 59, 8), ('!10.6', '10.6', 0, 0)] or
            winner['first_pc_divergence'] != 107 or
            winner['high']['a_3f9'] != [10] or winner['high']['i_3f9'] != [21] or
            winner['high']['y_distinct_after_8'] != {'3F8':6, '3F9':6, '3FA':6}):
        raise ValueError('PROM data source screen changed')
    mapping, upper = upper_winner
    selected = [row for row in upper['trace'] if row['pc'] == ROM_PC]
    values = [row['external_read']['value'] for row in selected]
    replay = run_trace(mapping, base, replay=values)
    if replay['result']['trace_digest'] != upper['result']['trace_digest']:
        raise ValueError('explicit 3F7 replay does not reproduce the ROM run')
    rom = (HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin').read_bytes()
    address = selected[PULSE_VISIT]['external_read']['address']
    alternate = rom[address-256]
    changed = values[:]
    changed[PULSE_VISIT] = alternate
    impulse = run_trace(mapping, base, replay=changed)
    first_y = first_difference([row['alu']['y'] for row in replay['trace']],
                               [row['alu']['y'] for row in impulse['trace']])
    first_pc = first_difference([row['pc'] for row in replay['trace']],
                                [row['pc'] for row in impulse['trace']])
    if (address != 0x117 or values[PULSE_VISIT] != 0x44 or alternate != 0x33 or
            first_y != 288 or first_pc != 307 or
            replay['trace'][306]['next_pc'] != 0x3EA or
            impulse['trace'][306]['next_pc'] != 0x3EE or
            impulse['result']['address_counts'].get(ROM_PC, 0) != 33):
        raise ValueError('isolated PROM data route byte-to-branch result changed')
    paths = [Path(__file__), HERE/'lower_i_input_pipeline.py',
             HERE/'independent_slice_addresses.py', HERE/'independent_slice_fields.py',
             HERE/'split_slice_probe.py', HERE/'photo_controller_path.py',
             HERE.parent/'assumed/execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2]/'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='read-valid PROM data-bit source alternatives, not recovered wiring',
                  fixture=dict(cycles=CYCLES, q=5, initial_ram=[0]*16,
                               lower_i6_source='11.0',
                               enable_assumptions='U10 E2=0, U11 E4=1',
                               shared_pin_pairs='I7/A0 and I0/A1'),
                  cases=cases,
                  isolated_byte=dict(visit=PULSE_VISIT, rom_address=address,
                                     original_byte=values[PULSE_VISIT],
                                     alternate_byte=alternate,
                                     replay_matches_rom=True,
                                     first_y_divergence=first_y,
                                     first_pc_divergence=first_pc,
                                     branch_cycle=306, original_next_pc='3EA',
                                     changed_next_pc='3EE',
                                     changed_3f7_visits=33,
                                     trace_digests=dict(replay=replay['result']['trace_digest'],
                                                        impulse=impulse['result']['trace_digest'])),
                  limitations=[
                      'U10 D6 through U6 D0/Q0 to I7/A0, U11 D2 through U5 D0/Q0 to I0/A1 and the U10-D6 inversion are untraced alternatives to the photographed enable-side continuations.',
                      'Valid PROM read enable levels are assumed; the emulator does not model their physical clock or latch hold here.',
                      'The loop does not consume the controller bitstream or expose a traced DAC output.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['cases']:
        print(row['i7_a0'], row['i0_a1'],
              row['high']['selected_3f7'], row['low']['selected_3f7'],
              row['first_pc_divergence'])
    print(report['isolated_byte'])
