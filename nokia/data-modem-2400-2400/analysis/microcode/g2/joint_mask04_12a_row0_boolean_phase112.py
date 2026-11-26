"""Challenge frozen 20-state row gates on fresh data at another R1 phase."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_row0_boolean_gain as gain

HERE = Path(__file__).resolve().parent
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
OUT = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
PAYLOADS = {'40': (0x3A, 0xC7, 0x95, 0xE0, 0x6D, 0x12, 0xB4, 0x5F),
            '60': (0xD6, 0x09, 0x7B, 0xA4, 0x21, 0xFE, 0x58, 0xC3)}
OFFSET = 112


def run(out=OUT):
    with patch.object(gain, 'LOGIC', LOGIC), \
            patch.object(gain, 'PAYLOADS', PAYLOADS), \
            patch.object(gain, 'OFFSET', OFFSET), \
            patch.object(gain, 'LEVELS', (1.0,)):
        report = gain.run(out=out)
    report['experiment'] = 'frozen 20-state row-phase gates on new payloads at R1 offset 112'
    report['fixture']['phase_model'] = LOGIC.name
    report['fixture']['levels'] = (1.0,)
    report['limitations'].append(
        'The 20-state gates were fixed before these payloads and the offset-112 challenge; no state labels were refit.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
