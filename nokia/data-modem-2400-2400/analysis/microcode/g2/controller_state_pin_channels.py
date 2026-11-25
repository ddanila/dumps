"""Execute A0/A1/A2 sends and retain the independent P1 output channel."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from controller_frames import (ANALYSIS, CORE, ROM, INITIAL_P1, INITIAL_SP,
                               CYCLE_LIMIT, STOP, command_line)
from photo_cd4094_order import shift_four_bytes

HERE = Path(__file__).resolve().parent
STATES = ('A0', 'A1', 'A2')
EXPECTED = {'A0': ('80 02 88 7A', 1),
            'A1': ('80 02 81 7A', 0),
            'A2': ('80 02 88 7A', 0)}


def run(out=HERE / 'results/controller-state-pin-channels.json'):
    saved = json.loads((HERE / 'results/controller-frames.json').read_text())
    digest = hashlib.sha256(ROM.read_bytes()).hexdigest()
    if saved['controller_rom_sha256'] != digest:
        raise ValueError('controller frame report uses a different ROM')
    by_state = {row['state']: row for row in saved['rows'] if row['state'] in STATES}
    sources = [Path(__file__), ANALYSIS / 'interface_probe.c',
               ANALYSIS / 'controller_output.py',
               *[CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c')]]
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'probe'
        subprocess.run(['cc', '-O2', '-Wall', '-DSAT_TRACE', '-I', str(CORE),
                        str(ANALYSIS / 'interface_probe.c'),
                        *map(str, sources[3:]), '-o', str(exe)], check=True)
        process = subprocess.run(
            [str(exe), str(ROM), str(INITIAL_P1), '0',
             str(CYCLE_LIMIT), str(STOP), str(INITIAL_SP)],
            input=''.join(command_line(int(state, 16)) for state in STATES),
            text=True, capture_output=True, check=True)
    executions = [json.loads(line) for line in process.stdout.splitlines()]
    if len(executions) != len(STATES):
        raise ValueError('controller did not execute all states')
    rows = []
    for state, execution in zip(STATES, executions):
        events = execution['events']
        frame = bytes(event['value'] for event in events if event['kind'] == 'tx')
        completions = [event for event in events if event['kind'] == 'tx_complete']
        p1 = [event for event in events if event['kind'] == 'p1']
        latch_high = [event for event in p1 if event['value'] & 4]
        expected_frame, expected_bit = EXPECTED[state]
        code = int(by_state[state]['code'], 16)
        if (execution['errors'] or not execution['reached_stop'] or
                execution['pc'] != 0x1EE8 or len(frame) != 4 or
                len(completions) != 4 or len(latch_high) != 1 or
                latch_high[0]['cycle'] <= completions[-1]['cycle'] or
                frame.hex(' ').upper() != expected_frame or
                by_state[state]['wire'] != expected_frame or
                ((execution['p1'] >> 5) & 1) != expected_bit or
                ((code >> 1) & 1) != expected_bit or
                ((latch_high[0]['value'] >> 5) & 1) != expected_bit):
            raise ValueError(f'{state} frame/P1 execution changed')
        chips = shift_four_bytes(frame)
        rows.append(dict(state=state, code=f'{code:02X}',
                         frame=expected_frame, final_p1=f'{execution["p1"]:02X}',
                         p1_5=expected_bit,
                         p1_events=[dict(cycle=event['cycle'],
                                         value=f'{event["value"]:02X}')
                                    for event in p1],
                         last_tx_complete_cycle=completions[-1]['cycle'],
                         latch_high_cycle=latch_high[0]['cycle'],
                         cd4094_q8_chip1=f'{chips[1]["q8_to_d0"]:02X}'))
    if (rows[0]['frame'] != rows[2]['frame'] or
            rows[0]['p1_5'] == rows[2]['p1_5'] or
            len({(row['frame'], row['p1_5']) for row in rows}) != 3):
        raise ValueError('frame/P1 state distinction changed')
    report = dict(status='executed controller frame and P1.5 state channels',
                  controller_rom_sha256=digest,
                  fixture=dict(entry='1EE2', initial_p1=f'{INITIAL_P1:02X}',
                               initial_sp=INITIAL_SP,
                               flags_payload='fixed controller-frames fixture',
                               serial_completions='synthetic after each send'),
                  rows=rows,
                  finding='A0 and A2 send identical four-byte frames, but P1.5 differs; frame plus P1.5 distinguishes A0/A1/A2 in this fixture.',
                  limitations=[
                      'These are separate send-routine entries under one fixed RAM/flag fixture, not a natural uninterrupted state chain.',
                      'P1.5 electrical destination, CD4094 cascade and DSC2847 input route are untraced.',
                      'The result identifies an additional controller channel, not its tone or training meaning.'],
                  source_sha256={str(path.relative_to(ANALYSIS.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    for row in run()['rows']:
        print(row['state'], row['frame'], row['final_p1'], row['p1_5'])
