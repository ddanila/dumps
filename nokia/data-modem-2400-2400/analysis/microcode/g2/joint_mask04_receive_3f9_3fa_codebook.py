"""Classify the once-per-ADC-visit 3F9/3FA Y outputs."""

import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from execute import execute
from joint_mask04_receive_impulse_memory import ADC_VISITS, CYCLES, held_samples
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_carrier_phase_screen import rotated_transmit
from reference_modem import receive

DIBITS = (3, 1, 0, 2, 3, 2, 1, 0)
DEGREES = (0, 45, 90)
SITES = ('3F9', '3FA')


def capture(mapping, base, adc):
    scenario = configured(base, adc, 'previous', 'overflow', 1)
    visits = []
    current = None
    with tempfile.TemporaryDirectory() as tmp:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=tmp, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
            raise ValueError('receive path changed')
        for line in (Path(tmp) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            if pc == 0x3F8:
                if current is not None:
                    raise ValueError('previous visit was incomplete')
                current = {}
                if row['external_read']['value'] != adc[len(visits)]:
                    raise ValueError('ADC selection changed')
            elif pc in (0x3F9, 0x3FA):
                if current is None:
                    continue  # Initial wrapper before the first selected ADC read.
                site = f'{pc:03X}'
                if site in current:
                    raise ValueError('3F9/3FA executed more than once per ADC visit')
                current[site] = row['alu']['y']
            elif pc == 0x3FE:
                if current is None:
                    continue
                if any(site not in current for site in SITES):
                    raise ValueError('3F9/3FA schedule changed')
                visits.append(current)
                current = None
    if len(visits) != ADC_VISITS or current is not None:
        raise ValueError('ADC visit count changed')
    return visits, result


def run(out=HERE / 'results/joint-mask04-receive-3f9-3fa-codebook.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    by_current = {site: defaultdict(set) for site in SITES}
    by_pair = {site: defaultdict(set) for site in SITES}
    cases = []
    for degrees in DEGREES:
        pcm = rotated_transmit(DIBITS, degrees)
        if receive(pcm) != list(DIBITS[1:]):
            raise ValueError('reference waveform does not carry intended dibits')
        adc = held_samples([127 - value for value in pcm], 0, None)
        visits, result = capture(mapping, base, adc)
        for i, visit in enumerate(visits):
            current = adc[i] >> 4
            previous = adc[i - 1] >> 4 if i else None
            for site in SITES:
                value = visit[site]
                by_current[site][current].add(value)
                if previous is not None:
                    by_pair[site][(previous, current)].add(value)
        cases.append(dict(degrees=degrees,
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          trace_digest=result['trace_digest'],
                          visit_y_sha256=hashlib.sha256(bytes(
                              visit[site] for visit in visits for site in SITES
                          )).hexdigest(),
                          cycles=result['completed_cycles']))
    codebooks = {}
    for site in SITES:
        current = by_current[site]
        pair = by_pair[site]
        codebooks[site] = dict(distinct_values=len(set().union(*current.values())),
                               current_nibbles=len(current),
                               observed_adjacent_pairs=len(pair),
                               max_values_per_current=max(map(len, current.values())),
                               current_conflicts=sum(len(x) > 1 for x in current.values()),
                               max_values_per_pair=max(map(len, pair.values())),
                               pair_conflicts=sum(len(x) > 1 for x in pair.values()),
                               values_by_current={f'{nibble:X}':
                                                  [f'{value:02X}' for value in sorted(values)]
                                                  for nibble, values in sorted(current.items())})
    report = dict(experiment='once-per-visit 3F9/3FA Y dependence on current and previous ADC nibble',
                  fixture=dict(dibits=DIBITS, degrees=DEGREES,
                               adc_visits_per_case=ADC_VISITS,
                               cycles_per_case=CYCLES,
                               adc='complementary legal reference PCM, 47/46 held visits'),
                  cases=cases, codebooks=codebooks,
                  limitations=[
                      'Observed codebooks are limited to three legal waveforms and the direct D3EB=01 mask04 fixture.',
                      'A single-valued output by ADC nibble does not imply an actual board latch or received-bit decision.',
                      'A current/previous-pair codebook does not rule out longer history outside these streams.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
