"""Challenge the frozen six-bit rule with both Y captures one visit late."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_frozen_sixth_new_payloads as frozen
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from receiver_mask04_offset_visit_phase import project

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-sixth-late-capture.json'


def phase96(pair):
    if pair != (frozen.PHASE_VISIT, 32):
        raise ValueError(f'unexpected original phase fixture: {pair}')
    return capturing_execute((pair[0], 96))


def late_project(symbols, first, second):
    if (first, second) != (46, 93):
        raise ValueError(f'unexpected original capture visits: {(first, second)}')
    return project(symbols, 47, 94)


def run(out=OUT):
    with patch.object(frozen, 'capturing_execute', phase96), \
            patch.object(frozen, 'project', late_project), \
            patch.object(frozen, 'LEVELS', (1.0,)):
        report = frozen.run(out=out)
    report['experiment'] = 'frozen six-bit rule at phase 96 with Y captures one visit late'
    report['fixture']['phase_offset'] = 96
    report['fixture']['capture_visits'] = [47, 94]
    report['limitations'].append(
        'Both capture points are one PROM visit later than development; '
        'this tests a clock hypothesis, not a measured board edge.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
