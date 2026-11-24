"""Screen candidate PROM-enable latch levels against real DSC2847 execution."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture, BASE_MAPPING, BASE_SCENARIO, PHOTO_RECORD, PHOTO_A_RECORD


def levels(scenario, e2, e4):
    result = copy.deepcopy(scenario)
    result['name'] += f'; candidate latched E2={e2} E4={e4}'
    result['evidence'] = ('Photo-inferred U10 E2→U5 Q0→U2 I0/A1 and '
                          'U11 E4→U6 Q0→U2 I7/A0; latch phase is untraced.')
    result['inputs']['instruction_bit_overrides']['0']['value'] = e2
    result['inputs']['instruction_bit_overrides']['7']['value'] = e4
    result['inputs']['register_address_bit_overrides']['a']['0']['value'] = e4
    result['inputs']['register_address_bit_overrides']['a']['1']['value'] = e2
    for policy in result['inputs']['instruction_bit_overrides'].values():
        policy['evidence'] = result['evidence']
    for policy in result['inputs']['register_address_bit_overrides']['a'].values():
        policy['evidence'] = result['evidence']
    return result


def run(out):
    mapping, base = fixture()
    cases = []
    for e2 in (0, 1):
        for e4 in (0, 1):
            scenario = levels(base, e2, e4)
            final_pcs = Counter()
            active = []
            output_visits = 0
            for q in range(256):
                scenario['initial']['q'] = q
                result = execute(mapping, scenario, 512, mode='integrated', trace_limit=0)
                if not result['clean']:
                    raise ValueError(f'unclean startup: E2={e2} E4={e4} Q={q}')
                final_pcs[f'{result["final_state"]["pc"]:03X}'] += 1
                if result['address_counts'].get(0x38E, 0):
                    active.append(q)
                output_visits += result['address_counts'].get(0x392, 0)
            cases.append(dict(e2=e2, e4=e4, active_q=active,
                              final_pcs=dict(sorted(final_pcs.items())),
                              output_392_visits=output_visits,
                              prom_read_simultaneously_valid=(e2 == 0 and e4 == 1)))
    if ([len(case['active_q']) for case in cases] != [0, 32, 0, 32]
            or [case['output_392_visits'] for case in cases] != [0, 0, 0, 1248]):
        raise ValueError('enable-level startup classes changed')

    _, bits = controller_stream()
    sustained = []
    for e2 in (0, 1):
        scenario = levels(base, e2, 1)
        scenario['initial']['q'] = 5
        scenario['io']['read']['pc_sequences']['910'] = bits
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, 1580, mode='integrated',
                             out=temporary, trace_limit=1580)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        input_rows = [row for row in trace if row['pc'] == 0x38E]
        if not result['clean'] or [row['external_read']['value'] for row in input_rows] != bits:
            raise ValueError(f'controller input not consumed for E2={e2}')
        first_input_cycle = input_rows[0]['cycle']
        rom = defaultdict(list)
        output = defaultdict(list)
        for row in trace:
            if row['cycle'] <= first_input_cycle:
                continue
            read = row.get('external_read', {})
            if read.get('selected_by_alu') and 'address' in read:
                rom[f'{row["pc"]:03X}'].append(read['address'])
            if row['pc'] in (0x392, 0x396):
                output[f'{row["pc"]:03X}'].append(row['alu']['y'])
        sustained.append(dict(e2=e2, e4=1, bits=len(bits), clean=result['clean'],
                              recurring_rom_addresses={pc: addresses for pc, addresses in sorted(rom.items())},
                              candidate_output_y={pc: values for pc, values in sorted(output.items())},
                              final_q=result['final_state']['q'],
                              trace_digest=result['trace_digest']))
    if set(sustained[0]['recurring_rom_addresses']) or set(sustained[1]['recurring_rom_addresses']) != {'389', '38A', '38C'}:
        raise ValueError('ROM recurrence differs from enable-level prediction')
    if any(len(set(addresses[1:])) != 1 for addresses in sustained[1]['recurring_rom_addresses'].values()):
        raise ValueError('ROM address did not settle after first input')
    sources = [Path(__file__), BASE_MAPPING, BASE_SCENARIO, PHOTO_RECORD, PHOTO_A_RECORD,
               HERE/'photo_controller_path.py', HERE/'controller_bit_dispatch.py',
               ASSUMED/'execute.py', ASSUMED/'common.py', HERE.parent/'model.py']
    report = dict(status='diagnostic latch-level sensitivity, not recovered timing',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources},
                  startup_cases=cases, controller_stream_cases=sustained,
                  limitations=['E2 high disables U10 PROM output in the documented read phase; ordinary U10 data fields cannot simultaneously be assumed valid.',
                               'A different latch phase or held output would need an explicit timing circuit; neither is established by the photographs.',
                               'ROM enable/address, Q=5 and D38E serial timing remain untraced assumptions.',
                               'ALU Y at 392/396 has no identified physical output connection.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-enable-timing.json')
    print([(case['e2'], case['e4'], len(case['active_q']), case['output_392_visits'])
           for case in report['startup_cases']])
