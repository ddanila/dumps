"""Challenge frozen 22-state row gates at a new carrier start and payload."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_row0_twentytwo_holdout as holdout

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-row0-twentytwo-phase120.json'
PAYLOADS = {'40': (0x2D, 0x91, 0xE6, 0x4B, 0x70, 0xAF, 0x13, 0xC8),
            '60': (0xB6, 0x05, 0xD9, 0x32, 0x8F, 0x41, 0xEC, 0x7A)}
OFFSET = 120


def run(out=OUT):
    with patch.object(holdout, 'PAYLOADS', PAYLOADS), \
            patch.object(holdout, 'OFFSET', OFFSET):
        report = holdout.run(out=out)
    report['experiment'] = 'frozen 22-state gates and +5 line shift on fresh phase-120 payloads'
    report['limitations'].append(
        'The 22-state gates, +5 line shift and fixed gain were chosen without these payloads or this phase start.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
