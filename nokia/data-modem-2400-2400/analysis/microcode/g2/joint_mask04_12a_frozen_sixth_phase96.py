"""Challenge the frozen six-bit rule at an untrained carrier start."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_frozen_sixth_new_payloads as frozen
from joint_mask04_tx_12a_delayed_latch import capturing_execute

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/joint-mask04-12a-frozen-sixth-phase96.json'


def phase96(pair):
    if pair != (frozen.PHASE_VISIT, 32):
        raise ValueError(f'unexpected original phase fixture: {pair}')
    return capturing_execute((pair[0], 96))


def run(out=OUT):
    # Keep the original payload, gain, receiver feature and 91-key table fixed.
    # The patched factory changes only the one-time running R1 phase offset.
    with patch.object(frozen, 'capturing_execute', phase96):
        report = frozen.run(out=out)
    report['experiment'] = 'frozen six-bit rule on third payloads at phase offset 96'
    report['fixture']['phase_offset'] = 96
    report['limitations'].append(
        'This wrapper changes only the running R1 offset from 32 to 96; '
        'the offset is a diagnostic intervention, not a verified board input.')
    report['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
