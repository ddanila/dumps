"""Challenge frozen 12-state mode gates at a further carrier start."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase128-challenge.json'
PAYLOADS = {
    '40': (0x17, 0xC4, 0x9B, 0x2E, 0xD0, 0x6A, 0xF5, 0x83),
    '60': (0xB2, 0x08, 0x7D, 0xE1, 0x4F, 0x93, 0x25, 0xCA),
}
OFFSET = 128


def run(out=OUT):
    with patch.object(fresh, 'MODEL', MODEL), \
            patch.object(fresh, 'PAYLOADS', PAYLOADS), \
            patch.object(fresh, 'OFFSET', OFFSET):
        report = fresh.run(out=out)
    report['experiment'] = 'frozen 12-state changed-mode gate on new phase-128 controller payloads'
    report['fixture']['phase_model'] = MODEL.name
    report['limitations'].append(
        'The 12-state covers, mode edge, line gain and shift were frozen before this phase-128 challenge.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
