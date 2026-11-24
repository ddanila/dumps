"""Screen raw PROM output edges as direct clocks at table consumers."""

import hashlib
import statistics
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
import execute as executor
from common import read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_controller_dibits import CONTROLLER
from photo_table_prombit_consumer import bit_decode
from photo_table_prombit_symbols import scenario
from photo_table_restart_dibits import trace_run

SEEDS = (155, 183, 184)
CHIPS = ('10', '11', '17', '18')
CONSUMERS = (0x140, 0x146)


def edges(trace, lane, bit, rising):
    return [index for index in range(1, len(trace))
            if ((trace[index - 1]['raw'][lane] >> bit) & 1) == (1 - rising)
            and ((trace[index]['raw'][lane] >> bit) & 1) == rising]


def run(out=HERE / 'results/photo-output-clock-bit-screen.json'):
    groups = read(CONTROLLER)['groups']
    mapping = mapped(MAPPINGS['q3'])
    runs = []
    with tempfile.TemporaryDirectory() as temporary, patch.object(executor, 'decode', bit_decode):
        directory = Path(temporary)
        for seed in SEEDS:
            for group in groups:
                state = scenario({str(0x349): group['line_bytes']})
                result, trace, restarts = trace_run(mapping, state, seed, directory)
                consumer_indexes = [index for index, row in enumerate(trace)
                                    if row['pc'] in CONSUMERS]
                if not consumer_indexes or len(restarts) != 15:
                    raise ValueError('consumer/diagnostic fixture changed')
                bits = []
                for lane, chip in enumerate(CHIPS):
                    for bit in range(8):
                        for rising in (0, 1):
                            indexes = edges(trace, lane, bit, rising)
                            hits = set(indexes) & set(consumer_indexes)
                            gaps = [b - a for a, b in zip(indexes, indexes[1:])]
                            values = [trace[index]['alu']['y'] for index in indexes]
                            bits.append(dict(chip=chip, bit=bit,
                                             edge='rising' if rising else 'falling',
                                             edges=len(indexes),
                                             consumer_hits=len(hits),
                                             distinct_y=len(set(values)),
                                             nonzero_y=sum(bool(value) for value in values),
                                             median_gap=statistics.median(gaps) if gaps else None))
                runs.append(dict(seed=seed, controller_selector=group['selectors'][0],
                                 consumer_visits=len(consumer_indexes),
                                 consumer_cycles=[trace[index]['cycle']
                                                  for index in consumer_indexes],
                                 bits=bits, trace_digest=result['trace_digest']))
    common = []
    summaries = []
    for chip in CHIPS:
        for bit in range(8):
            for edge in ('rising', 'falling'):
                rows = [next(row for row in run['bits']
                             if (row['chip'], row['bit'], row['edge']) == (chip, bit, edge))
                        for run in runs]
                summary = dict(chip=chip, bit=bit, edge=edge,
                               consumer_hits=sum(row['consumer_hits'] for row in rows),
                               edge_count_range=[min(row['edges'] for row in rows),
                                                 max(row['edges'] for row in rows)],
                               median_gap_range=[min(row['median_gap'] for row in rows),
                                                 max(row['median_gap'] for row in rows)],
                               distinct_y_range=[min(row['distinct_y'] for row in rows),
                                                 max(row['distinct_y'] for row in rows)],
                               nonzero_y_range=[min(row['nonzero_y'] for row in rows),
                                                max(row['nonzero_y'] for row in rows)])
                summaries.append(summary)
                if all(row['consumer_hits'] == run['consumer_visits']
                       for row, run in zip(rows, runs)):
                    common.append(summary)
    expected_common = {('10', 2, 'falling'), ('10', 4, 'falling'),
                       ('11', 1, 'rising'), ('11', 3, 'rising'),
                       ('17', 3, 'rising'), ('17', 5, 'rising'),
                       ('18', 3, 'rising'), ('18', 7, 'rising')}
    if (len(runs) != 12 or
            sum(run['consumer_visits'] for run in runs) != 56 or
            {(row['chip'], row['bit'], row['edge']) for row in common}
            != expected_common):
        raise ValueError('clock-screen fixture changed')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_prombit_consumer.py',
             HERE / 'photo_table_prombit_symbols.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='diagnostic direct-PROM-bit clock screen',
                  fixture=dict(mapping='q3', seeds=list(SEEDS),
                               controller_selectors=[group['selectors'][0]
                                                     for group in groups],
                               cycles=2500, candidate_u5_d0='inverted U10 bit 5',
                               candidate_d349='controller bytes by visit',
                               diagnostic_rst_pulses=15,
                               clock='edge on one raw data output of U10, U11, U17 or U18',
                               candidate_latch_data='Am2901 Y',
                               consumers=['140', '146']),
                  common_consumer_edge_bits=common,
                  bit_summaries=summaries,
                  runs=[{key: value for key, value in row.items() if key != 'bits'}
                        for row in runs],
                  limitations=[
                      'A PROM data output is not a traced 74LS273 clock net; a decoder or external divider could change the edge schedule.',
                      'The 375-1500 cycle spacing is conditional on a 14.4 MHz/k microcycle for k=1..4 and a 9600 Hz sample rate.',
                      'D349 input, U5 inversion/capture, previous-Y branch bus and diagnostic AC=RST are untraced assumptions.',
                      'The screen tests direct single-bit clocks only, not decoded clocks, DAC bus wiring or a modem waveform.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(x['chip'], x['bit'], x['edge'],
            *x['edge_count_range'])
           for x in report['common_consumer_edge_bits']])
