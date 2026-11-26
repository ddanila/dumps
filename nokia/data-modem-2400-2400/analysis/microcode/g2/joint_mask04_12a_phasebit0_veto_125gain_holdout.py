"""Hold out the 2F veto term on new phase-131 high-gain payloads."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_phase137_holdout as prior

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-phasebit0-veto-125gain-holdout.json'
GAIN = HERE / 'results/joint-mask04-12a-mode-phase131-gain-fixture.json'
OFFSET = 131
FACTOR = 1.25
PAYLOADS = {
    '40': (0x5E, 0x03, 0xB8, 0x71, 0xD4, 0x2F, 0xA6, 0xC9),
    '60': (0xE0, 0x49, 0x1D, 0xB3, 0x67, 0x8A, 0xF5, 0x20),
}


def run(out=OUT):
    with patch.object(prior, 'OFFSET', OFFSET), \
            patch.object(prior, 'GAIN', GAIN), \
            patch.object(prior, 'FACTOR', FACTOR), \
            patch.object(prior, 'PAYLOADS', PAYLOADS):
        report = prior.run(out=out)
    report['experiment'] = ('frozen two-term phase-bit-0 veto on fresh '
                            'phase-131 1.25x controller payloads')
    report['limitations'].append(
        'The high-gain PCM may clip; the count is reported per run. The payloads were fixed before this challenge and both veto terms remain frozen.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
