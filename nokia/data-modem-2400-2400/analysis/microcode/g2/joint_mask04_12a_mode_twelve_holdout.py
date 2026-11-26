"""Challenge frozen 12-state mode gates on a separate phase-120 payload pair."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
OUT = HERE / 'results/joint-mask04-12a-mode-twelve-holdout.json'
PAYLOADS = {
    '40': (0x5A, 0xC3, 0x1F, 0xE0, 0x74, 0x8B, 0x26, 0xD9),
    '60': (0xE7, 0x02, 0xB4, 0x69, 0x3D, 0xF0, 0x85, 0x1C),
}


def run(out=OUT):
    with patch.object(fresh, 'MODEL', MODEL), \
            patch.object(fresh, 'PAYLOADS', PAYLOADS):
        report = fresh.run(out=out)
    report['experiment'] = 'frozen 12-state changed-mode gate on new phase-120 controller payloads'
    report['fixture']['phase_model'] = MODEL.name
    report['limitations'].append(
        'These payloads were fixed after the 12-state gates and were not used to choose their Boolean covers.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
