"""Test a small fixed chip-1 logic decode for controller tone/data modes."""

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from photo_12c_divided_state_latch import profile
from photo_12c_prom_edge_latch import run_trace
from photo_127_liveness import ROM
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac
from photo_main_frame_carrier_swap import spectrum
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

STATE_REPORT = HERE / 'results/controller-state-pin-channels.json'
MAIN_REPORT = HERE / 'results/main-loop-serial.json'
MODES = ('state_A0', 'state_A1', 'state_A2',
         'main_00', 'main_20', 'main_40', 'main_60',
         'chain_A1', 'chain_A2')
SAMPLES = 640


def decode_chip1(raw):
    capture_enable = raw & 1
    mode = (raw >> 5) & 1
    d127 = (1 << 7) | (mode << 5) | (mode << 4) | ((1 - mode) << 3)
    return capture_enable, mode, d127


def projected_codes(rom, step, offset=0):
    return tuple(q_to_dac((phase - rom[256 + phase]) & 255, 'swap_q4_q5')
                 for phase in ((3 + (1 + offset + sample * 375) * step) & 255
                               for sample in range(SAMPLES)))


def run(out=HERE / 'results/photo-controller-mode-decode.json'):
    frames = frames_from_reports()
    state_report = json.loads(STATE_REPORT.read_text())
    main_report = json.loads(MAIN_REPORT.read_text())
    chain_frames = {'A1': [], 'A2': []}
    for row in main_report['rows']:
        for state, frame in zip(row['states'], row['frames']):
            if state in chain_frames:
                chain_frames[state].append(frame)
    if ({state: (len(values), set(values)) for state, values in
         chain_frames.items()} != {
             'A1': (512, {'80 02 A1 7A'}),
             'A2': (512, {'80 02 A8 7A'})}):
        raise ValueError('preserved-controller-chain A1/A2 frames changed')
    frames.update({f'chain_{state}': bytes.fromhex(values[0])
                   for state, values in chain_frames.items()})
    p1 = {f'state_{row["state"]}': row['p1_5']
          for row in state_report['rows']}
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for name in MODES:
        frame = frames[name]
        chips = shift_four_bytes(frame)
        raw = chips[1]['q8_to_d0']
        enabled, mode, step = decode_chip1(raw)
        if (name.startswith('state_') and
                (enabled, mode, step) !=
                ((1, 0, 0x88) if name == 'state_A1' else (0, 0, 0x88))):
            raise ValueError('state-mode decode changed')
        if name.startswith('main_') and (enabled, mode, step) != (1, 1, 0xB0):
            raise ValueError('main-mode decode changed')
        if name == 'chain_A1' and (enabled, mode, step) != (1, 1, 0xB0):
            raise ValueError('preserved-chain A1 counterexample changed')
        if name == 'chain_A2' and (enabled, mode, step) != (0, 1, 0xB0):
            raise ValueError('preserved-chain A2 counterexample changed')
        result, trace = run_trace(mapping, base, step, chips[0]['q8_to_d0'])
        reads = [row for row in trace if row['pc'] == 0x129]
        if (not result['clean'] or len(reads) != 740 or
                any(row['pc'] == 0x12E for row in trace)):
            raise ValueError('decoded carrier/tone loop changed')
        for n, row in enumerate(reads, 1):
            phase = (3 + n * step) & 255
            byte = rom[256 + phase]
            if (row['external_read']['address'] != 256 + phase or
                    row['external_read']['value'] != byte or
                    row['alu']['y'] != (phase - byte) & 255):
                raise ValueError('decoded loop ROM/Y recurrence changed')
        dac = projected_codes(rom, step)
        period = 256 // math.gcd(step, 256)
        rotations = {dac[i:] + dac[:i] for i in range(period)}
        if any(projected_codes(rom, step, offset) not in rotations
               for offset in range(period)):
            raise ValueError('decoded output phase alignment changed')
        tone = profile(dac) if mode == 0 else spectrum(dac)
        if enabled and tone['peak_hz'] != (2100 if mode == 0 else 1800):
            raise ValueError('decoded output rate changed')
        cases.append(dict(controller_mode=name, frame=frame.hex(' ').upper(),
                          p1_5=p1.get(name),
                          logical_chip1=f'{raw:02X}',
                          chip1_bit0=enabled, chip1_bit5=mode,
                          decoded_d127=f'{step:02X}',
                          capture_enabled=bool(enabled),
                          pc129_reads=len(reads),
                          hypothetical_capture_count=SAMPLES if enabled else 0,
                          full_dac_code_if_clocked=tone,
                          first_16_codes_if_clocked=[f'{value:02X}'
                                                     for value in dac[:16]],
                          phase_alignments_checked=period,
                          trace_digest=result['trace_digest']))
    if (len({row['trace_digest'] for row in cases if row['chip1_bit5'] == 0}) != 1 or
            len({row['trace_digest'] for row in cases if row['chip1_bit5'] == 1}) != 1):
        raise ValueError('decoded mode path diverged within the same mode')
    paths = [Path(__file__), STATE_REPORT, MAIN_REPORT, ROM,
             HERE / 'results/controller-frames.json',
             HERE.parents[2] / 'analysis/controller/OUTPUT32.md',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_12c_prom_edge_latch.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_main_frame_carrier_swap.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             HERE.parent / 'board/inventory.json']
    report = dict(status='isolated A1 and preserved-chain A1 select different hypothetical chip-1 modes',
                  fixture=dict(mapping='q3 photo-swapped',
                               controller='ROM-executed isolated A0/A1/A2 sends, four main-loop frame classes and all preserved-chain A1/A2 sends',
                               chip1='logical CD4094 chip 1 Q8→D0',
                               logic='enable=raw bit0; mode=raw bit5; D127 bits 7,5,4,3 = 1,mode,mode,NOT mode; others zero',
                               rom_bank='upper at PC129',
                               sample_hz=9600, samples=SAMPLES,
                               microinstruction_divisor=1,
                               candidate_dac='Y129→LS273 ordered; Q4/Q5 swapped to DAC08',
                               photographed_logic_candidates='DSC U13 LS04 inverter and U4 LS244 buffer; no traced net assignment'),
                  preserved_chain_counts={state: len(values)
                                          for state, values in chain_frames.items()},
                  cases=cases,
                  limitations=[
                      'The CD4094 cascade, chip1-to-DSC route, fan-out/inversion gates, bit0 output qualification, DAC bus and 9600 Hz clock are hypotheses.',
                      'No physical U13/U4 connection to these bits is established; only the package types are photographed.',
                      'A0/A2 hypothetical capture suppression leaves the physical DAC held value and analog coupling unspecified.',
                      'Only 740 PC129 reads per mode are executed; 640 divided output codes project their checked recurrence.',
                      'The isolated A1 state-send fixture emits 81, whereas the preserved controller chain emits A1 in all 512 tested A1 sends; chip-1 bit5 is a controller counter-phase flag, not a proven tone/data mode bit.',
                      'The preserved chain uses synthetic receive events and timer underflow, so it is not a complete natural-duration operating sequence.',
                      'The A1=2100 Hz and main=1800 Hz labels remain provisional, and no USART dibit phase modulation or receiver/echo path is shown.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['controller_mode'], row['logical_chip1'],
              row['decoded_d127'], row['capture_enabled'],
              row['full_dac_code_if_clocked']['peak_hz'])
