"""Compare executed controller octet classes with V.26 ter rate-pattern rotations."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from pattern_classes import run as run_classifier
from state_transitions import CORE, HERE, ROM

STANDARD = 'https://search.itu.int/history/HistoryDigitalCollectionDocLibrary/4.259.43.en.1036.pdf'
# ITU-T V.26 ter (11/88), section 6.1.3, the 34 representative octets.
RATE_OCTETS = (0x01, 0x03, 0x05, 0x07, 0x09, 0x0B, 0x0D, 0x0F,
               0x11, 0x13, 0x15, 0x17, 0x19, 0x1B, 0x1D, 0x1F,
               0x25, 0x27, 0x2B, 0x2D, 0x2F, 0x33, 0x35, 0x37,
               0x3B, 0x3D, 0x3F, 0x55, 0x57, 0x5B, 0x5F, 0x6F,
               0x77, 0x7F)


def rotations(value):
    return {((value << shift) | (value >> (8 - shift))) & 0xFF
            for shift in range(8)}


def marked(classes):
    return {int(value, 16) for key, values in classes.items() if key != '00'
            for value in values}


def run():
    observed = run_classifier()
    groups = observed['groups']
    first_five = set().union(*(rotations(value) for value in RATE_OCTETS[:5]))
    first_two = set().union(*(rotations(value) for value in RATE_OCTETS[:2]))
    all_legal = set().union(*(rotations(value) for value in RATE_OCTETS))
    state83, statea6 = marked(groups['83']), marked(groups['A6'])
    assert len(RATE_OCTETS) == 34 and len(all_legal) == 254
    assert state83 == first_five and statea6 == first_two
    by_base = {}
    for value in RATE_OCTETS[:5]:
        orbit = rotations(value)
        by_base[f'{value:02X}'] = {
            state: {key: len(orbit & {int(x, 16) for x in values})
                    for key, values in groups[state].items() if key != '00'}
            for state in ('83', 'A6')}
    sequences = {
        'three_03': ([0x03]*3, 0x83, 3),
        'four_03': ([0x03]*4, 0x84, 4),
        'four_rotated_03': ([0x06]*4, 0x84, 4),
        'four_05': ([0x05]*4, 0x84, 4),
        'interrupted_03': ([0x03, 0x03, 0x01, 0x03], 0x83, 1),
        'four_unmarked_11': ([0x11]*4, 0x83, 0),
    }
    chains = {}
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary)/'chain-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-function',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE/'rate_pattern_chain_probe.c'),
                        *(str(CORE/name) for name in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for name, (octets, state, count) in sequences.items():
            result = json.loads(subprocess.run(
                [str(exe), str(ROM), *(str(value) for value in octets)],
                text=True, capture_output=True, check=True).stdout)
            assert (result['errors'], result['state_after'], result['equal_count']) == (0, state, count)
            assert [row['byte'] for row in result['octets']] == octets
            chains[name] = result
    paths = [Path(__file__), HERE/'pattern_classes.py', HERE/'pattern_probe.c',
             HERE/'rate_pattern_chain_probe.c', HERE.parents[1]/'interface_probe.c',
             *(CORE/name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')), ROM]
    return dict(status='exact octet-set match; controller detector purpose is unproven',
                standard=STANDARD, standard_section='ITU-T V.26 ter (11/88) 6.1.3',
                rate_octets=[f'{value:02X}' for value in RATE_OCTETS],
                distinct_legal_rotations=len(all_legal),
                observed_marked={'83': len(state83), 'A6': len(statea6)},
                exact_match={'83': 'rotations of 01,03,05,07,09',
                             'A6': 'rotations of 01,03'},
                by_base=by_base,
                preserved_ram_chains=chains,
                controller_fixture=observed['preconditions'],
                interpretation=('The executed classifier accepts exactly the first five '
                                'V.26 ter rate-pattern rotation classes in state 83 and '
                                'the first two in state A6. The full standard list covers '
                                '254 nonconstant bytes, so this is a selective match.'),
                limitations=['The local routine runs do not prove that RAM3A contains a rate-pattern octet in operation.',
                             'The four-octet chains preserve RAM between classifier calls but direct the PC to each entry point; they are not an uninterrupted controller call.',
                             'Earlier receive processing and the physical source of the octet are not exercised in these chains.',
                             'No DSC2847 microcode or line signal is executed.'],
                source_sha256={str(path.relative_to(HERE.parents[4])):
                               hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/rate-pattern-match.json')
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], result['observed_marked'])


if __name__ == '__main__':
    main()
