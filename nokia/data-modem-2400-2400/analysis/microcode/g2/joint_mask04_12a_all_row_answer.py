"""Run the all-row 3ED latch test on the independent answer-side payload."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_all_row_latch as base

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-all-row-answer.json'
PAYLOAD = (0x9C, 0x41, 0xF6, 0x28, 0xB3, 0x0D, 0x75, 0xEA)


def run(out=OUT):
    with patch.object(base, 'SELECTOR', '60'), \
            patch.object(base, 'DELAY', 18), \
            patch.object(base, 'PAYLOAD', PAYLOAD):
        report = base.run(out=out)
    report['experiment'] = 'all four executed 3ED rows in the answer-side fresh receive stream'
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
