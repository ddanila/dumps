"""Feed consecutive unchanged-8031 A4/A5 write bits through joined DSC Tx/Rx."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_joined_a4_data as joined
from controller_segment2_pattern import standard_bits
from joint_mask04_12a_a4_phase_training import pack_lsb

HERE = Path(__file__).resolve().parent
CONTROLLER = HERE / 'results/main-loop-long.json'


def aligned_bytes(run):
    writes = [(row['state'], int(byte, 16))
              for row in run['iterations'] for byte in row['line_bytes']]
    if len(writes) < 17 or [state for state, _ in writes[:17]] != \
            ['A4'] * 8 + ['A5'] * 9:
        raise ValueError(('controller A4/A5 write sequence changed', run['selector']))
    bits = [(value >> bit) & 1 for _, value in writes for bit in range(8)]
    shifted = bits[1:129]
    if len(shifted) != 128:
        raise ValueError('controller write stream too short')
    return [sum(shifted[8 * index + bit] << bit for bit in range(8))
            for index in range(16)]


def run(out=HERE / 'results/joint-mask04-12a-controller-continuation.json'):
    controller = json.loads(CONTROLLER.read_text())
    streams = {}
    for selector, polynomial in (('40', 'GPC'), ('60', 'GPA')):
        row = next(run for run in controller['runs'] if run['selector'] == selector)
        streams[selector] = aligned_bytes(row)
        if streams[selector][:8] != pack_lsb(standard_bits(polynomial)):
            raise ValueError(('standard A4 window changed', selector))

    def continuation(_payload, delay):
        if delay not in (5, 18):
            raise ValueError(('unexpected controller selector delay', delay))
        return streams['40' if delay == 5 else '60'][8:]

    with patch.object(joined, 'line_octets', continuation):
        report = joined.run(out)
    for case in report['cases']:
        expected = streams[case['selector']]
        observed = [int(value, 16) for value in
                    case['training_line_bytes'] + case['payload_line_bytes']]
        if observed != expected:
            raise ValueError(('joined line differs from controller writes',
                              case['selector']))
    report['experiment'] = 'consecutive unchanged-8031 A4/A5 writes through joined real-PROM DSC Tx/Rx'
    report['fixture']['serial'] = (
        'first 129 bits of consecutive A4/A5 port-01 writes from one '
        '64-iteration unchanged-8031 run, aligned at bit 1')
    report['fixture']['controller_source'] = CONTROLLER.name
    report['limitations'] = [
        'The controller run forces timer expiry and readies port status at polling boundaries.',
        'Port-01 writes are assumed to reach TxD in order; a 17-byte paced 8251 transmit run is not established.',
        'The bit-1 alignment, R1 phase intervention, converter buses, line filter, ADC path and receive phase logic are assumptions.',
        'The 16-byte reverse 8251/8031 handoff is not modeled here.']
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = \
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['source_sha256'][str(CONTROLLER.relative_to(HERE.parents[4]))] = \
        hashlib.sha256(CONTROLLER.read_bytes()).hexdigest()
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
