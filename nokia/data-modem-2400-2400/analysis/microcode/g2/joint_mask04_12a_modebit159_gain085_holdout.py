"""Fresh lower-level challenge of the frozen 159-state phase witness."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_modebit159_revised_holdout as prior

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OFFSET = 203
FACTOR = 0.85
PAYLOADS = {
    '40': (0x3B, 0xD6, 0x81, 0x4F, 0xA9, 0x02, 0x75, 0xEC),
    '60': (0xC7, 0x14, 0xE8, 0x5A, 0x93, 0x6D, 0x20, 0xBF),
}
GAIN = RESULTS / 'joint-mask04-12a-modebit159-gain085-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-modebit159-gain085-holdout.json'


def run(out=OUT):
    with patch.object(prior, 'OFFSET', OFFSET), \
            patch.object(prior, 'FACTOR', FACTOR), \
            patch.object(prior, 'PAYLOADS', PAYLOADS), \
            patch.object(prior, 'GAIN', GAIN):
        report = prior.run(out=out)
    report['experiment'] = 'fresh offset-203 0.85x challenge of frozen 159-state thirteen-bit cover'
    report['limitations'] = [
        item.replace('only offset-201 is untouched validation',
                     'offset-201 and offset-203 were untouched validations')
        for item in report['limitations']]
    report['limitations'].append(
        'The phase witness was frozen before offset-203; physical input, capture, gate and serial nets remain assumed.')
    source = str(Path(__file__).relative_to(HERE.parents[4]))
    report['source_sha256'][source] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for mode in ('edge32', 'edge48'):
        path = RESULTS / f'joint-mask04-12a-modebit159-gain115-holdout-{mode}-{OFFSET}.json'
        target = RESULTS / f'joint-mask04-12a-modebit159-gain085-holdout-{mode}-{OFFSET}.json'
        raw = json.loads(path.read_text())
        raw['experiment'] = 'fresh 0.85x real-PROM frozen thirteen-bit mode-boundary challenge'
        raw['source_sha256'][source] = report['source_sha256'][source]
        target.write_text(json.dumps(raw, indent=2) + '\n')
        path.unlink()
        del report['source_sha256'][str(path.relative_to(HERE.parents[4]))]
        report['source_sha256'][str(target.relative_to(HERE.parents[4]))] = (
            hashlib.sha256(target.read_bytes()).hexdigest())
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
