"""Compare a high-RAM return at the second available D site, 3FC."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from joint_mask04_ram_carry_propagation import fixtures, paired_case
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS


def run(out=HERE / 'results/joint-mask04-ram-carry-3fc-propagation.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = [paired_case(execute, mapping, base, *args, read_pc=0x3FC)
             for args in fixtures()]
    report = dict(experiment='full-word propagation of previous-carry high-RAM return at 3FC',
                  fixture=dict(condition='previous carry, polarity 1',
                               route='3F9 Y high nibble -> sample-paced RAM -> -3 sample 3FC D high nibble',
                               control='same writes and address clock without readback',
                               contrast='3FB is a reached Am27S31 read; 3FC is a scenario D read'),
                  cases=cases,
                  limitations=[
                      'The RAM-to-D mux, TEST source and output wiring are photo-compatible hypotheses.',
                      'Propagation into later PROM arithmetic does not establish a falling echo residual.',
                      'Only the varying 64-sample and mixed 192-sample legal streams are tested here.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
