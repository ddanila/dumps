"""Challenge the frozen veto on a new lower-gain carrier family."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_phase137_holdout as prior

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-phasebit0-veto-lowgain133-challenge.json'
GAIN = HERE / 'results/joint-mask04-12a-mode-phase133-lowgain-fixture.json'
OFFSET = 133
FACTOR = 0.8
PAYLOADS = {
    '40': (0x73, 0xC8, 0x1A, 0xEF, 0x04, 0xB9, 0x52, 0xD6),
    '60': (0xAD, 0x26, 0xF1, 0x48, 0x95, 0x0B, 0xE3, 0x7C),
}


def run(out=OUT):
    with patch.object(prior, 'OFFSET', OFFSET), \
            patch.object(prior, 'GAIN', GAIN), \
            patch.object(prior, 'FACTOR', FACTOR), \
            patch.object(prior, 'PAYLOADS', PAYLOADS):
        report = prior.run(out=out)
    report['experiment'] = ('frozen two-term phase-bit-0 veto on fresh '
                            'phase-133 0.8x real-PROM controller streams')
    report['limitations'].append(
        'Carrier offset 133, 0.8x calibrated gain and both payloads were fixed before this challenge; the correction remains frozen.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
