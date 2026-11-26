"""Challenge raw DSC transmit MSB phase with fresh ROM-scrambled data bytes."""

import copy
import hashlib
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parents[1]
sys.path[:0] = [str(ANALYSIS), str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from controller_scrambler import transform
from interface_study import CORE, ROM as CONTROLLER_ROM, SHA as CONTROLLER_SHA
from joint_four_row_retention_tx import (
    MAPPINGS, candidate, fixture, hold_candidate, mapped,
    mapping_with_upper_source, split_scenario,
)
from joint_mask04_msb_data_phase import score as phase_score
from joint_mask04_dac_msb_data import score as filtered_score
from joint_mask04_msb_segment1_phase import (
    CARRIER_HZ, TONE_HZ, half_turn_error, successive_angles, symbol_phasors,
)
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP,
    TONE_SYMBOLS, TOTAL_SYMBOLS,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs

EXECUTE = HERE.parent / 'assumed/execute.py'
SITES = (0x127, 0x128, 0x129, 0x12A)
START_CYCLE = 40
CYCLES_PER_SAMPLE = 1500
SAMPLES = TOTAL_SYMBOLS * 8
CYCLES = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
HISTORIES = {'40': 0x654321, '60': 0x13579B}
PAYLOAD_SEEDS = {'40': 0xA140, '60': 0xA160}


def capture_execute():
    """Instrument one isolated copy of the emulator at the established sample edge."""
    source = EXECUTE.read_text()
    patches = (
        ("    source_read=scenario['io']['read'];table=source_read['table'];rom_hash=None",
         "    source_read=scenario['io']['read'];table=source_read['table'];rom_hash=None\n"
         "    sample_streams={0x127:[],0x128:[],0x129:[],0x12A:[]}"),
        ("            carry_input.observe(result)",
         "            sample_offset=cycle-40\n"
         "            if sample_offset>=0 and sample_offset//1500<832 and sample_offset%1500<4:\n"
         "                expected_pc=0x127+sample_offset%1500\n"
         "                if pc!=expected_pc: raise ValueError(('sample loop left',cycle,pc,expected_pc))\n"
         "                sample_streams[pc].append(result['y'])\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['candidate_samples']={f'{pc:03X}':values for pc,values in sample_streams.items()}\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection site changed', old))
        source = source.replace(old, new)
    scope = {'__name__': 'joint_mask04_fresh_payload_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def controller_bytes(executable, selector):
    delay = 18 if selector == '40' else 5
    history = HISTORIES[selector]
    generator = random.Random(PAYLOAD_SEEDS[selector])
    plaintext = [generator.randrange(256) for _ in range(9)]
    prior = bytearray(6)
    prior[2] = int(delay == 5)
    lines = []
    predictions = []
    for value in plaintext:
        frame = bytes((history >> 16, (history >> 8) & 255,
                       history & 255, value, 0, 2))
        lines.append(f'scram {frame.hex()} {prior.hex()} 8 0\n')
        history, output = transform(history, value, delay)
        predictions.append((history, output))
    result = subprocess.run([str(executable), str(CONTROLLER_ROM),
                             '248', '0', '256', '8192', '113'],
                            input=''.join(lines), text=True,
                            capture_output=True, check=True)
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    if len(rows) != len(plaintext):
        raise ValueError('controller execution count changed')
    wire = []
    for row, (expected_history, expected_byte) in zip(rows, predictions):
        ram = row['iram']
        actual_history = (ram[0x3F] << 16) | (ram[0x40] << 8) | ram[0x41]
        if (row['errors'] or not row['returned'] or
                (actual_history, ram[0x38]) != (expected_history, expected_byte)):
            raise ValueError(('controller ROM scrambler mismatch', selector))
        wire.append(ram[0x38])
    bits = [(byte >> bit) & 1 for byte in wire for bit in range(8)]
    data_bits = bits[1:65]
    dibits = [(data_bits[index] << 1) | data_bits[index + 1]
              for index in range(0, 64, 2)]
    return plaintext, wire, dibits


def execute_symbols(execute, mapping, base, dibits):
    symbols = [3] * SEGMENT_SYMBOLS + dibits
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; fresh ROM-scrambled payload at candidate D127'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    result = execute(mapping, scenario, CYCLES, mode='integrated', trace_limit=0)
    streams = result.pop('candidate_samples')
    if not result['clean'] or any(len(values) != SAMPLES for values in streams.values()):
        raise ValueError(('fresh payload did not sustain sample loop',
                          result['clean'], {pc: len(v) for pc, v in streams.items()}))
    msb = {pc: bytes(value & 0x80 for value in mapped_codes(raw, SELECTED))
           for pc, raw in streams.items()}
    if len(set(msb.values())) != 1:
        raise ValueError('candidate MSB depends on latch phase')
    codes = mapped_codes(streams['129'], SELECTED)
    tone = successive_angles(symbol_phasors(codes, 0, TONE_HZ))
    segment = successive_angles(symbol_phasors(
        codes, TONE_SYMBOLS + SILENCE_SYMBOLS, CARRIER_HZ))
    phase = phase_score(codes, dibits, -1)
    opposite_phase = phase_score(codes, dibits, 1)
    filtered = filtered_score([value & 0x80 for value in codes], symbols)
    return dict(trace_digest=result['trace_digest'],
                msb_sha256=hashlib.sha256(msb['129']).hexdigest(),
                msb=msb['129'],
                tone_max_abs_phase_degrees=max(abs(x) for x in tone),
                segment1_max_half_turn_error_degrees=max(
                    half_turn_error(x) for x in segment),
                phase=phase,
                opposite_phase=opposite_phase,
                filtered_reference=filtered,
                d127_visits=result['read_sequence_visits'].get(0x127),
                selected_rom_reads=result['rom_reads']['selected_by_alu'])


def run(out=HERE / 'results/joint-mask04-fresh-controller-payload.json'):
    if hashlib.sha256(CONTROLLER_ROM.read_bytes()).hexdigest() != CONTROLLER_SHA:
        raise ValueError('controller ROM hash changed')
    execute = capture_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        executable = Path(temporary) / 'controller-probe'
        probe = ANALYSIS / 'interface_probe.c'
        subprocess.run(['cc', '-O2', '-Wall', '-DSAT_TRACE', '-I', str(CORE),
                        str(probe), *(str(CORE / name) for name in
                                      ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(executable)], check=True,
                       capture_output=True, text=True)
        for selector in ('40', '60'):
            plaintext, wire, dibits = controller_bytes(executable, selector)
            active = execute_symbols(execute, mapping, base, dibits)
            control = execute_symbols(execute, mapping, base, [0] * 32)
            control_against_payload = phase_score(list(control['msb']), dibits, -1)
            data_start = (TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * 8
            differing_msb = sum(a != b for a, b in zip(
                active['msb'][data_start:], control['msb'][data_start:]))
            if (active['phase']['wrong_quadrants'] or
                    active['phase']['max_error_degrees'] >= 45 or
                    active['tone_max_abs_phase_degrees'] >= 45 or
                    active['segment1_max_half_turn_error_degrees'] >= 5 or
                    active['opposite_phase']['wrong_quadrants'] == 0 or
                    control_against_payload['wrong_quadrants'] == 0 or
                    differing_msb == 0):
                raise ValueError(('fresh controller payload did not modulate', selector))
            cases.append(dict(selector=selector, initial_history=HISTORIES[selector],
                              plaintext_bytes=[f'{x:02X}' for x in plaintext],
                              rom_scrambled_bytes=[f'{x:02X}' for x in wire],
                              dibits=dibits,
                              trace_digest=active['trace_digest'],
                              msb_sha256=active['msb_sha256'],
                              zero_data_control_trace_digest=control['trace_digest'],
                              zero_data_control_msb_sha256=control['msb_sha256'],
                              data_msb_samples_different_from_zero=differing_msb,
                              tone_max_abs_phase_degrees=active['tone_max_abs_phase_degrees'],
                              segment1_max_half_turn_error_degrees=
                                  active['segment1_max_half_turn_error_degrees'],
                              data_phase=active['phase'],
                              opposite_sign_wrong_quadrants=
                                  active['opposite_phase']['wrong_quadrants'],
                              zero_control_wrong_quadrants_against_payload=
                                  control_against_payload['wrong_quadrants'],
                              filtered_reference=active['filtered_reference'],
                              d127_visits=active['d127_visits'],
                              selected_rom_reads=active['selected_rom_reads']))
            print(selector, 'data errors', active['phase']['wrong_quadrants'],
                  'max phase error', round(active['phase']['max_error_degrees'], 2),
                  'MSB differences', differing_msb, flush=True)
    paths = (Path(__file__), EXECUTE, CONTROLLER_ROM,
             ANALYSIS / 'interface_probe.c',
             ANALYSIS / 'controller_scrambler.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'joint_mask04_msb_data_phase.py',
             HERE / 'joint_mask04_dac_msb_data.py',
             HERE / 'joint_mask04_msb_segment1_phase.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='fresh ROM-scrambled payload in joint mask04 raw MSB transmitter',
                  fixture=dict(mapping='joint upper-source lower mask04',
                               sample_edge='one capture per 1500 microinstructions at 127-12A',
                               sample_rate_hz=9600,
                               A1='32 symbols, 2100 Hz candidate step',
                               A3='32 symbols of 180-degree reversals',
                               data='32 dibits from locally ROM-executed 8031 scrambler, bit offset one',
                               candidate='Y7 to DAC08 B1 via assumed latch',
                               control='same A1/A3 with 32 zero data dibits'),
                  cases=cases,
                  limitations=['Fresh controller bytes are ROM-executed locally, not emitted by a timed uninterrupted main loop.',
                               'The bit-one alignment and D127 parity/phase rule are assumed interface wiring.',
                               'DAC latch clock/data route, current output and physical line path remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
