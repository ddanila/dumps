"""Challenge the frozen phase-bit-0 veto at a further carrier offset."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_phase137_holdout as prior

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-phasebit0-veto-phase139-challenge.json'
OFFSET = 139
PAYLOADS = {
    '40': (0x3C, 0xA7, 0x12, 0xD9, 0x45, 0xF0, 0x6E, 0x8B),
    '60': (0xC1, 0x58, 0xE3, 0x0A, 0xB6, 0x2D, 0x94, 0x7F),
}


def run(out=OUT):
    with patch.object(prior, 'OFFSET', OFFSET), \
            patch.object(prior, 'PAYLOADS', PAYLOADS):
        report = prior.run(out=out)
    report['experiment'] = ('frozen phase-bit-0 veto at carrier offset 139, '
                            'new payloads and 1.15x receive gain')
    report['limitations'].append(
        'The offset and payloads were fixed before this run; the two veto terms and gain remain frozen.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
