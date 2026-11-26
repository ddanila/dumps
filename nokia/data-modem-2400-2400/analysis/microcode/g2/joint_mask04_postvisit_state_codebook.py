"""Check whether settled receive state retains history beyond current ADC nibble."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from joint_mask04_receive_impulse_memory import (
    ADC_VISITS, CHANNELS, capture, held_samples,
)
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import transmit

HERE = Path(__file__).resolve().parent
DIBITS = {
    'varying': (3, 1, 0, 2, 3, 2, 1, 0),
    'rotated': (0, 1, 3, 2, 0, 2, 3, 1),
    'constant': (0,) * 8,
}


def run(out=HERE / 'results/joint-mask04-postvisit-state-codebook.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    by_nibble = defaultdict(set)
    streams = {}
    for name, dibits in DIBITS.items():
        samples = [127 - value for value in transmit(dibits)]
        values = held_samples(samples, 0, None)
        rows, trace = capture(mapping, base, values)
        local = defaultdict(set)
        for adc, row in zip(values, rows):
            state = bytes(row[4:])  # Q and R0..R15 at the row-3 3FE word.
            nibble = adc >> 4
            by_nibble[nibble].add(state)
            local[nibble].add(state)
        streams[name] = dict(dibits=dibits, adc_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                             visited_nibbles=sorted(local),
                             max_states_per_nibble=max(map(len, local.values())), **trace)
    codebook = {
        f'{nibble:X}': [dict(zip(CHANNELS[4:], state)) for state in sorted(states)]
        for nibble, states in sorted(by_nibble.items())
    }
    report = dict(fixture='direct D3EB=01, mask04, held 47/46 ADC visits per sample',
                  streams=streams, visits_per_stream=ADC_VISITS,
                  max_states_per_nibble=max(map(len, by_nibble.values())),
                  distinct_states=len(set().union(*by_nibble.values())),
                  codebook=codebook)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
