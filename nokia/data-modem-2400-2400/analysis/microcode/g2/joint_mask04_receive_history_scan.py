"""Locate receive-loop Y/Q sites with prior-sample dependence on legal PCM."""

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

CASES = (
    ('varying', (3, 1, 0, 2, 3, 2, 1, 0), 0),
    ('varying', (3, 1, 0, 2, 3, 2, 1, 0), 45),
    ('varying', (3, 1, 0, 2, 3, 2, 1, 0), 90),
    ('alternate', (0, 1, 3, 2, 0, 2, 3, 1), 0),
    ('alternate', (0, 1, 3, 2, 0, 2, 3, 1), 45),
)
CHANNELS = ('y', 'q', 'ram')


def capture(mapping, base, adc):
    scenario = configured(base, adc, 'previous', 'overflow', 1)
    visits = []
    current = None
    ram = scenario['initial']['ram'][:]
    with tempfile.TemporaryDirectory() as tmp:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=tmp, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
            raise ValueError('receive path changed')
        for line in (Path(tmp) / 'trace.jsonl').open():
            row = json.loads(line)
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if row['pc'] == 0x3F8:
                if current is not None:
                    if len(current) != 32:
                        raise ValueError('ADC visit is not 32 words')
                    visits.append(current)
                current = []
                if row['external_read']['value'] != adc[len(visits)]:
                    raise ValueError('ADC byte changed at selection')
            if current is not None:
                current.append((row['pc'], row['alu']['y'], row['q'], bytes(ram)))
    if len(visits) != ADC_VISITS - 1 or not (0 < len(current) <= 32):
        raise ValueError('complete ADC visit count changed')
    return visits, result


def run(out=HERE / 'results/joint-mask04-receive-history-scan.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    grouped = {(offset, channel): defaultdict(dict)
               for offset in range(32) for channel in CHANNELS}
    paired = {(offset, channel): defaultdict(set)
              for offset in range(32) for channel in CHANNELS}
    pc_template = None
    cases = []
    for name, dibits, degrees in CASES:
        pcm = rotated_transmit(dibits, degrees)
        if receive(pcm) != list(dibits[1:]):
            raise ValueError('reference receiver lost intended dibits')
        adc = held_samples([127 - value for value in pcm], 0, None)
        visits, result = capture(mapping, base, adc)
        for i, visit in enumerate(visits):
            pcs = tuple(row[0] for row in visit)
            if pc_template is None:
                pc_template = pcs
            elif pcs != pc_template:
                raise ValueError('receive PC path changed by waveform')
            if i == 0:
                continue  # Previous ADC sample is undefined at this edge.
            current = adc[i] >> 4
            previous = adc[i - 1] >> 4
            for offset, (_, y, q, ram) in enumerate(visit):
                for channel, value in (('y', y), ('q', q), ('ram', ram)):
                    # Save one causal witness for each value under a current bin.
                    grouped[(offset, channel)][current].setdefault(
                        value, dict(stream=name, degrees=degrees, visit=i,
                                    previous=f'{previous:X}', current=f'{current:X}',
                                    value=(value.hex() if isinstance(value, bytes)
                                           else f'{value:02X}')))
                    paired[(offset, channel)][(previous, current)].add(value)
        cases.append(dict(stream=name, dibits=dibits, degrees=degrees,
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          trace_digest=result['trace_digest'],
                          complete_visits=len(visits), cycles=result['completed_cycles']))
    sites = []
    for offset, pc in enumerate(pc_template):
        for channel in CHANNELS:
            current_groups = grouped[(offset, channel)]
            pair_groups = paired[(offset, channel)]
            conflicts = [examples for examples in current_groups.values()
                         if len(examples) > 1]
            witness = None
            if conflicts:
                witness = list(next(iter(conflicts)).values())[:2]
            varying_registers = None
            if channel == 'ram':
                varying_registers = [index for index in range(16)
                                     if any(len({state[index] for state in examples}) > 1
                                            for examples in current_groups.values())]
            sites.append(dict(offset=offset, pc=f'{pc:03X}', channel=channel,
                              current_nibbles=len(current_groups),
                              current_conflicts=len(conflicts),
                              max_values_per_current=max(map(len, current_groups.values())),
                              observed_pairs=len(pair_groups),
                              pair_conflicts=sum(len(values) > 1 for values in pair_groups.values()),
                              varying_registers=varying_registers,
                              witness=witness))
    report = dict(experiment='Y/Q/RAM prior-sample dependence at each receive-loop word',
                  fixture=dict(streams=[name for name, _, _ in CASES],
                               degrees=[degrees for _, _, degrees in CASES],
                               cycles_per_case=CYCLES, adc_visits_per_case=ADC_VISITS,
                               complete_visits_scanned_per_case=ADC_VISITS - 2,
                               adc='complementary legal PCM, 47/46 visits per sample',
                               direct_mode='D3EB=01'),
                  cases=cases, sites=sites,
                  limitations=[
                      'The scan covers five eight-symbol legal waveforms and one modeled board mapping.',
                      'Dependence on the prior ADC nibble is input memory, not a proven received-bit decision.',
                      'Q, Y and RAM are internal or candidate external signals; their physical consumers remain untraced.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
