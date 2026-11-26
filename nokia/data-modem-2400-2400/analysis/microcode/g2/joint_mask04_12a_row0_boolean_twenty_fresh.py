"""Challenge revised 20-state phase gates on new data, phase and gain."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_row0_boolean_gain as gain

HERE = Path(__file__).resolve().parent
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
OUT = HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json'
PAYLOADS = {'40': (0x62, 0xE5, 0x19, 0xA7, 0xD0, 0x3B, 0x8F, 0x54),
            '60': (0x9C, 0x41, 0xF6, 0x28, 0xB3, 0x0D, 0x75, 0xEA)}
OFFSET = 88


def run(out=OUT):
    with patch.object(gain, 'LOGIC', LOGIC), \
            patch.object(gain, 'PAYLOADS', PAYLOADS), \
            patch.object(gain, 'OFFSET', OFFSET):
        report = gain.run(out=out)
    report['experiment'] = 'frozen 20-state row-phase gates on fresh payloads and gain at R1 offset 88'
    report['fixture']['phase_model'] = LOGIC.name
    report['limitations'].append(
        'The revised 20-state gates were fixed before these payloads, offset and line levels.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
