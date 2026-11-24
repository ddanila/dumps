"""Screen read-valid U10 data-bit alternatives for the U5 Q0→I0/A1 route."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import (BASE_MAPPING, BASE_SCENARIO,
                                   PHOTO_A_RECORD, PHOTO_RECORD, fixture)


def summarize(trace, threshold):
    rom, output = defaultdict(list), defaultdict(list)
    for row in trace:
        if row['cycle'] <= threshold:
            continue
        read = row.get('external_read', {})
        if read.get('selected_by_alu') and 'address' in read:
            rom[f'{row["pc"]:03X}'].append(read['address'])
        if row['pc'] in (0x392, 0x396):
            output[f'{row["pc"]:03X}'].append(row['alu']['y'])
    return ({pc: dict(visits=len(values), values=sorted(set(values)))
             for pc, values in sorted(rom.items())},
            {pc: dict(visits=len(values), values=sorted(set(values)))
             for pc, values in sorted(output.items())})


def run(out):
    base_mapping, base_scenario = fixture()
    _, bits = controller_stream()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        for bit in range(8):
            mapping = copy.deepcopy(base_mapping)
            scenario = copy.deepcopy(base_scenario)
            token = f'10.{bit}'
            mapping['name'] += f'-diagnostic-I0-A1-{token}'
            mapping['fields']['i']['bits'][0] = token
            mapping['fields']['a']['bits'][1] = token
            for field in ('i', 'a'):
                mapping['fields'][field]['status'] = 'hypothesis'
                mapping['fields'][field]['evidence'] = (
                    'Alternative U5 D0 source from U10 data bit; U5 Q0 fan-out '
                    'to I0/A1 is photo-inferred, source bit is untraced.')
            del scenario['inputs']['instruction_bit_overrides']['0']
            del scenario['inputs']['register_address_bit_overrides']['a']['1']
            scenario['name'] += f'; diagnostic U5 D0={token}, read-valid E2=0'
            scenario['initial']['q'] = 5
            scenario['io']['read']['pc_sequences']['910'] = bits
            path = Path(temporary) / str(bit)
            result = execute(mapping, scenario, 1580, mode='integrated',
                             out=path, trace_limit=1580)
            trace = [json.loads(line) for line in (path/'trace.jsonl').read_text().splitlines()]
            inputs = [row for row in trace if row['pc'] == 0x38e]
            consumed = [row['external_read']['value'] for row in inputs]
            if not result['clean'] or consumed != bits[:len(consumed)]:
                raise ValueError(f'unclean or mismatched controller run for {token}')
            first = inputs[0]['cycle'] if inputs else 1580
            second = inputs[1]['cycle'] if len(inputs) > 1 else 1580
            rom_after_first, output_after_first = summarize(trace, first)
            rom_after_second, output_after_second = summarize(trace, second)
            cases.append(dict(u5_d0_candidate=token, read_phase_e2=0,
                              input_bits_consumed=len(inputs), clean=result['clean'],
                              visits_392=result['address_counts'].get(0x392, 0),
                              visits_396=result['address_counts'].get(0x396, 0),
                              rom_after_first=rom_after_first,
                              output_after_first=output_after_first,
                              rom_after_second=rom_after_second,
                              output_after_second=output_after_second,
                              final_pc=f'{result["final_state"]["pc"]:03X}',
                              trace_digest=result['trace_digest']))
    if [case['input_bits_consumed'] for case in cases] != [128, 1, 128, 128, 128, 128, 128, 1]:
        raise ValueError('U10 data-bit path classes changed')
    if [bool(case['rom_after_first']) for case in cases] != [True, False, False, False,
                                                            False, False, False, False]:
        raise ValueError('unexpected recurring ROM site in data-bit screen')
    paths = [Path(__file__), HERE/'photo_controller_path.py',
             HERE/'controller_bit_dispatch.py', BASE_MAPPING, BASE_SCENARIO,
             PHOTO_RECORD, PHOTO_A_RECORD, ASSUMED/'execute.py', HERE.parent/'model.py']
    report = dict(status='photo-local source alternative, not traced wiring or transmitter proof',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths},
                  controller_bits=len(bits), initial_q=5, cases=cases,
                  limitations=['U5 D0 from any U10 data output is an alternative to, not confirmation of, the photo-inferred E2 route.',
                               'All eight bit assignments use the same assumed ROM gate, D38E controller input, Q=5 and output candidates.',
                               'No resulting path shows retained phase or a verified physical line-output stream.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-i0-data-screen.json')
    print([(row['u5_d0_candidate'], row['input_bits_consumed'],
            sorted(row['rom_after_first'])) for row in report['cases']])
