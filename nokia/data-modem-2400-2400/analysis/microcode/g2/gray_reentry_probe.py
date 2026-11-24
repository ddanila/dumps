"""Replay controller dibits through a hypothetical repeated q3 Gray-operand call."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent/'assumed'
sys.path[:0] = [str(HERE), str(ASSUMED)]
from common import read
from execute import execute
from sine_operand_study import scenario_for_phase

CONFIG = ASSUMED/'sine-operand-study.json'
CONTROLLER = HERE/'results/main-loop-serial.json'
SELECTORS = ('00', '20', '40', '60')


def dibits_from_bytes(values):
    # The controller's synchronous octets are presented least-significant bit first.
    bits = [(value >> bit) & 1 for value in values for bit in range(8)]
    return [bits[i] + 2*bits[i+1] for i in range(0, len(bits)-1, 2)]


def run_sequence(config, mapping, dibits):
    previous = None
    rows = []
    for index, dibit in enumerate(dibits[:20]):
        # The untraced bridge puts a 2-bit controller symbol into D316 with
        # the base that made the first diagnostic ROM address 07C..07F.
        scenario = scenario_for_phase(config, 'q3', 0x7C + dibit)
        scenario['name'] = f'G2 local q3 Gray reentry, symbol {index}'
        policy = scenario['io']['read']
        policy['address']['bank'] = 0
        policy['address']['evidence'] = (
            'Diagnostic lower-bank ROM read at 317, local PC345 reentry and '
            'D316=(0x77+controller dibit) bridge; none is a traced connection.')
        policy['evidence'] = policy['address']['evidence']
        if previous is not None:
            scenario['initial']['pc'] = 0x345
            scenario['initial']['ram'] = previous['ram']
            scenario['initial']['q'] = previous['q']
            policy['address']['initial_y'] = previous.get('previous_y', 0)
        cycles = 110 if index == 0 else 69
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, cycles, mode='integrated',
                             out=temporary, trace_limit=cycles)
            trace = [json.loads(line) for line in
                     (Path(temporary)/'trace.jsonl').read_text().splitlines()]
        reads = [row for row in trace if row['pc'] == 0x317]
        outputs = [row for row in trace if row['pc'] == 0x392]
        if (not result['clean'] or result['final_state']['pc'] != 0x84 or
                len(reads) != 1 or len(outputs) != 1):
            raise ValueError(('q3 reentry changed', index, result['final_state']['pc']))
        rows.append(dict(index=index, dibit=dibit,
                         initial_q=scenario['initial']['q'],
                         rom_address=reads[0]['external_read']['address'],
                         rom_byte=reads[0]['external_read']['value'],
                         candidate_output=outputs[0]['alu']['y'],
                         final_q=result['final_state']['q'],
                         trace_digest=result['trace_digest']))
        previous = result['final_state']
    return rows


def run():
    config = read(CONFIG)
    mapping = read(ASSUMED/config['profiles']['q3'])
    controller = read(CONTROLLER)
    if controller['distinct_streams'] != 4:
        raise ValueError('continuous controller stream report changed')
    cases = []
    for selector in SELECTORS:
        source = next(row for row in controller['rows'] if row['selector'] == selector)
        symbols = dibits_from_bytes(source['line_bytes'])
        rows = run_sequence(config, mapping, symbols)
        cases.append(dict(selector=selector, controller_bytes=source['line_bytes'],
                          controller_dibits=symbols[:20], rows=rows))
    for case in cases:
        rows = case['rows']
        if ([row['final_q'] for row in rows[8:]] !=
                [170 if i % 2 == 0 else 169 for i in range(8, 20)] or
            [row['candidate_output'] for row in rows[8:]] !=
                [80 if i % 2 == 0 else 82 for i in range(8, 20)]):
            raise ValueError('late q3 recurrence changed')
    sources = [Path(__file__), CONFIG, ASSUMED/config['profiles']['q3'],
               CONTROLLER, ASSUMED/'sine_operand_study.py', ASSUMED/'execute.py',
               ASSUMED.parent/'model.py']
    return dict(status='negative for the local q3 reentry and D316 bridge',
                hypothesis='Each controller dibit supplies D316=0x77+dibit; after the first reset path, PC345 is called once per dibit with RAM/Q and prior-Y retained; ROM317 uses bank 0; ALU Y at 392 is a candidate output.',
                cases=cases,
                finding='By symbol 8 all four tested controller streams settle to the same alternating Q=170/169 and output=80/82 despite differing dibits; ROM addresses remain near 020 rather than repeatedly visiting 07C..07F.',
                limitations=['D316 input bridge and repeated PC345 call are diagnostic hypotheses, not recovered board connections or natural control flow.',
                             'The candidate output is Am2901 Y, not a traced DAC byte or line waveform.',
                             'Other mappings, call paths and initial states remain possible.'],
                source_sha256={str(path.relative_to(HERE.parent)):
                               hashlib.sha256(path.read_bytes()).hexdigest() for path in sources})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/gray-reentry-probe.json')
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], [(case['selector'], len(case['rows'])) for case in result['cases']])


if __name__ == '__main__':
    main()
