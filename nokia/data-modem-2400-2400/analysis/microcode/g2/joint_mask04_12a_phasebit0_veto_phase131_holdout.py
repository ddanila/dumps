"""Hold out fresh payloads at the failing phase-131, 1.15x fixture."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_phase137_holdout as prior

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-phasebit0-veto-phase131-holdout.json'
OFFSET = 131
PAYLOADS = {
    '40': (0x84, 0x19, 0xF2, 0x5D, 0xA0, 0x3B, 0xC7, 0x6E),
    '60': (0x0B, 0xD4, 0x71, 0xCE, 0x28, 0x95, 0xF0, 0x63),
}


def run(out=OUT):
    with patch.object(prior, 'OFFSET', OFFSET), \
            patch.object(prior, 'PAYLOADS', PAYLOADS):
        report = prior.run(out=out)
    report['experiment'] = ('frozen two-term phase-bit-0 veto on new '
                            'phase-131, 1.15x controller payloads')
    report['limitations'].append(
        'This holdout keeps the previously failing phase/gain fixture but changes both payloads; the veto terms are frozen.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
