"""Identify which hypothesized E2-derived Am2901 pin opens the ROM path."""
import hashlib
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from photo_controller_path import (BASE_MAPPING, BASE_SCENARIO, PHOTO_A_RECORD,
                                   PHOTO_RECORD, fixture)
from photo_enable_timing import levels
from controller_bit_dispatch import controller_stream
from execute import execute
from common import save

HERE = Path(__file__).resolve().parent


def run(out):
    mapping, base = fixture()
    _, bits = controller_stream()
    cases = []
    for i0 in (0, 1):
        for a1 in (0, 1):
            # Split the candidate shared E2 route only as a sensitivity test.
            scenario = levels(base, 0, 1)
            scenario['name'] += f'; diagnostic split I0={i0} A1={a1}'
            scenario['inputs']['instruction_bit_overrides']['0']['value'] = i0
            scenario['inputs']['register_address_bit_overrides']['a']['1']['value'] = a1
            split_evidence = ('Diagnostic split of photo-inferred shared U10 E2 route; '
                              'I0/A1 independent levels are not recovered wiring.')
            scenario['inputs']['instruction_bit_overrides']['0']['evidence'] = split_evidence
            scenario['inputs']['register_address_bit_overrides']['a']['1']['evidence'] = split_evidence
            scenario['initial']['q'] = 5
            scenario['io']['read']['pc_sequences']['910'] = bits
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, 1580, mode='integrated',
                                 out=temporary, trace_limit=1580)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            inputs = [row for row in trace if row['pc'] == 0x38e]
            if not result['clean'] or [row['external_read']['value'] for row in inputs] != bits:
                raise ValueError(f'controller input incomplete for I0={i0} A1={a1}')
            first_input = inputs[0]['cycle']
            rom = defaultdict(list)
            outputs = defaultdict(list)
            for row in trace:
                if row['cycle'] <= first_input:
                    continue
                read = row.get('external_read', {})
                if read.get('selected_by_alu') and 'address' in read:
                    rom[f'{row["pc"]:03X}'].append(read['address'])
                if row['pc'] in (0x392, 0x396):
                    outputs[f'{row["pc"]:03X}'].append(row['alu']['y'])
            cases.append(dict(i0=i0, a1=a1, e2_read_phase=0, e4=1,
                              photo_shared_route_consistent=(i0 == a1 == 0),
                              input_bits=len(inputs),
                              visits_392=result['address_counts'].get(0x392, 0),
                              recurring_rom={pc: dict(visits=len(values), values=sorted(set(values)))
                                             for pc, values in sorted(rom.items())},
                              candidate_alu_y={pc: dict(visits=len(values), values=sorted(set(values)))
                                               for pc, values in sorted(outputs.items())},
                              trace_digest=result['trace_digest']))
    if ([case['visits_392'] for case in cases] != [57, 57, 71, 71]
            or [bool(case['recurring_rom']) for case in cases] != [False, False, True, True]):
        raise ValueError('I0 split no longer predicts ROM recurrence')
    paths = [Path(__file__), HERE/'photo_enable_timing.py', HERE/'photo_controller_path.py',
             HERE/'controller_bit_dispatch.py', BASE_MAPPING, BASE_SCENARIO,
             PHOTO_RECORD, PHOTO_A_RECORD, HERE.parent/'assumed/execute.py',
             HERE.parent/'model.py']
    report = dict(status='diagnostic pin sensitivity, not recovered wiring',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths},
                  controller_bits=len(bits), initial_q=5, cases=cases,
                  limitations=['Only I0=0, A1=0 preserves the photo-inferred shared E2 route in one read-valid phase.',
                               'The I0=1 cases require a different pin connection or explicitly modeled latch timing and held PROM data.',
                               'ROM gating, D38E controller input and physical output route remain assumptions.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    result = run(HERE/'results/photo-e2-split.json')
    print([(c['i0'], c['a1'], c['visits_392'], sorted(c['recurring_rom']))
           for c in result['cases']])
