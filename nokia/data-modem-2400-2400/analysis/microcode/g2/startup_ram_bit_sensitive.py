"""Check whether single-byte startup RAM changes animate the bit-sensitive path."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from instruction_bit_neighborhood import after_input_groups, score_groups
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

COARSE_VALUES = (0, 1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128, 255)


def run(out):
    mapping = mapped(MAPPINGS['q1'])
    mapping['fields']['i']['bits'][1] = '!10.5'
    _, base = fixture()
    _, bits = controller_stream()
    base['initial']['q'] = 5
    base['io']['read']['pc_sequences']['910'] = bits
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        trace_path = Path(temporary)
        for ram_index in range(16):
            values = range(256) if ram_index in (12, 13) else COARSE_VALUES
            for value in values:
                scenario = copy.deepcopy(base)
                scenario['initial']['ram'][ram_index] = value
                result = execute(mapping, scenario, 512, mode='integrated',
                                 out=trace_path, trace_limit=512)
                trace = [json.loads(line) for line in
                         (trace_path/'trace.jsonl').read_text().splitlines()]
                metrics = score_groups(after_input_groups(trace))
                metrics.pop('first_8_groups')
                rows.append(dict(ram_index=ram_index, value=value,
                                 clean=result['clean'],
                                 visits_38e=result['address_counts'].get(0x38E, 0),
                                 selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                 final_pc=f"{result['final_state']['pc']:03X}",
                                 final_q=result['final_state']['q'],
                                 final_ram12=result['final_state']['ram'][12],
                                 final_ram13=result['final_state']['ram'][13],
                                 trace_digest=result['trace_digest'], **metrics))
    if len(rows) != 736:
        raise ValueError('startup RAM sweep domain changed')
    class_counts = Counter((row['clean'], row['visits_38e'],
                            row['selected_rom_reads'], row['group_count'],
                            tuple(row['rom_patterns_per_bit'].values()),
                            tuple(row['output_patterns_per_bit'].values()),
                            row['output_byte_differs_between_bits']) for row in rows)
    evolving = [dict(ram_index=row['ram_index'], value=row['value']) for row in rows
                if any(n > 1 for n in row['rom_patterns_per_bit'].values()) or
                   any(n > 1 for n in row['output_patterns_per_bit'].values())]
    paths = [Path(__file__), HERE/'instruction_bit_neighborhood.py',
             HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py', HERE/'controller_bit_dispatch.py',
             ASSUMED/'execute.py', MAPPINGS['q1']]
    report = dict(status='single-RAM-byte startup sensitivity, not recovered startup state',
                  fixture=dict(mapping='q1 with I1=!10.5', initial_q=5,
                               input_pc='38E', controller_bits_offered=len(bits),
                               cycles=512, zero_other_ram=True,
                               coarse_values=list(COARSE_VALUES),
                               exhaustive_ram_indices=[12, 13]),
                  counts=dict(cases=len(rows), clean=sum(row['clean'] for row in rows),
                              classes=[dict(clean=key[0], input_visits=key[1],
                                            rom_reads=key[2], complete_groups=key[3],
                                            rom_patterns_per_bit=list(key[4]),
                                            output_patterns_per_bit=list(key[5]),
                                            output_byte_differs_between_bits=key[6],
                                            cases=count)
                                       for key, count in sorted(class_counts.items())],
                              evolving_cases=len(evolving)),
                  evolving_cases=evolving, rows=rows,
                  limitations=['Only one RAM byte changes from zero per run; combined initialization and later controller writes are not tested.',
                               'The mapping, ROM gate, Q=5 and D38E controller connection are hypothetical.',
                               'Candidate ALU-Y output has no traced DAC08HP connection.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/startup-ram-bit-sensitive.json')
    print(report['counts'])
