"""Match the failed phase-133 payloads at original receive gain."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_lowgain133_challenge as lowgain

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-phasebit0-veto-baseline133-control.json'
GAIN = HERE / 'results/joint-mask04-12a-mode-phase133-baseline-fixture.json'
FACTOR = 1.0


def run(out=OUT):
    with patch.object(lowgain, 'GAIN', GAIN), \
            patch.object(lowgain, 'FACTOR', FACTOR):
        report = lowgain.run(out=out)
    report['experiment'] = ('phase-133 matched controller payload control '
                            'at original calibrated gain')
    report['limitations'].append(
        'This control changes only receive gain relative to the 0.8x phase-133 challenge; the correction and payloads remain frozen.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
