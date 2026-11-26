"""Replay a package-budgeted, hypothetical receive phase circuit."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
INVENTORY = HERE.parent / 'board/inventory.json'
MODE0 = RESULTS / 'joint-mask04-12a-row0-boolean-twentytwo.json'
MODE1 = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
SAVED_RUNS = (
    (0, RESULTS / 'joint-mask04-12a-row0-boolean-twenty-fresh-88.json'),
    (1, RESULTS / 'joint-mask04-12a-mode-twelve-holdout.json'),
    (1, RESULTS / 'joint-mask04-12a-mode-phase128-challenge.json'),
)
OUT = RESULTS / 'photo-u15-u19-u21-phase-route.json'


def circuit(state, mode):
    """Return the two phase bits from the stated U13/U15/U19/U21 route."""
    s = [(state >> bit) & 1 for bit in range(7)]
    inv = [1 - bit for bit in s]
    not_mode = 1 - mode
    # U19 triple NAND, then U13 inverter: s0 & s2 & s3.
    u19_pre_nand = 1 - (s[0] & s[2] & s[3])
    pre = 1 - u19_pre_nand
    # U15 S64: ABCD + GHI + EF + JK, then one U13 inverter.
    abcd = inv[1] & inv[2] & inv[6] & not_mode
    ghi = inv[0] & inv[1] & s[6]
    ef = pre  # Other input tied high.
    jk = inv[0] & inv[2]
    u15_y = 1 - (abcd | ghi | ef | jk)
    bit0 = 1 - u15_y
    # U21 NOR and tied-input inverter form (mode | s6); U19 NAND
    # with its third input tied high forms NOT[s2 & (mode | s6)].
    u21_nor = 1 - (mode | s[6])
    u21_or = 1 - u21_nor
    bit1 = 1 - (s[2] & u21_or)
    return bit0 | (bit1 << 1)


def run(out=OUT):
    inventory = json.loads(INVENTORY.read_text())
    markings = {part['ref']: part['marking'] for part in inventory['parts']}
    required = {'U13': 'DM74LS04N', 'U15': 'SN74S64J',
                'U19': 'SN74LS10N', 'U21': 'HD74LS02P'}
    if any(markings.get(ref) != marking for ref, marking in required.items()):
        raise ValueError('photographed package inventory changed')
    models = [json.loads(path.read_text()) for path in (MODE0, MODE1)]
    labels = [model['state_phase' if mode == 0 else 'trained_state_phase']
              for mode, model in enumerate(models)]
    label_errors = []
    for mode, group in enumerate(labels):
        for code, expected in group.items():
            actual = circuit(int(code, 16), mode)
            if actual != expected:
                label_errors.append(dict(mode=mode, code=code,
                                         expected=expected, actual=actual))
    if label_errors:
        raise ValueError(('circuit differs from observed labels', label_errors))

    cases = []
    for mode, path in SAVED_RUNS:
        saved = json.loads(path.read_text())
        convention = models[mode]['fixture']['phase_convention']
        inverse = {step: dibit for dibit, step in enumerate(convention)}
        for case in saved['cases']:
            states = [sample_state(symbol, SELECTED)
                      for symbol in case['multi_visit_symbols']]
            phase = [circuit(state, mode) for state in states]
            decoded = [inverse[(after - before) & 3]
                       for before, after in zip(phase, phase[1:])]
            expected = case['expected_dibits'][1:]
            wrong = [index for index, (got, want) in
                     enumerate(zip(decoded, expected), 1) if got != want]
            if len(decoded) != len(expected):
                raise ValueError(('symbol count changed', path, case['selector']))
            unseen = sorted(f'{state:02X}' for state in
                            set(states) - {int(k, 16) for k in labels[mode]})
            if wrong or unseen:
                raise ValueError(('saved replay changed', path.name,
                                  case['selector'], wrong, unseen))
            cases.append(dict(source=path.name, mode=mode,
                              selector=case['selector'],
                              level=case.get('level'),
                              states=len(states),
                              distinct_states=len(set(states)),
                              unseen_states=unseen,
                              errors=len(wrong), wrong_indices=wrong,
                              source_rx_trace_digest=case['rx_trace_digest']))
    paths = (Path(__file__), INVENTORY, MODE0, MODE1,
             *(path for _, path in SAVED_RUNS))
    report = dict(
        experiment='photographed package-budgeted phase circuit replay',
        fixture=dict(
            inputs='seven assumed U12/U14/U3 state bits plus assumed D3EB mode bit',
            mode_mapping={'01': 0, '81/A1': 1},
            u15_terms=['~s1 & ~s2 & ~s6 & ~mode', '~s0 & ~s1 & s6',
                       's0 & s2 & s3 (precomputed)', '~s0 & ~s2'],
            outputs=['phase bit 0 = inverted U15 Y',
                     'phase bit 1 = NAND(s2, OR(mode, s6))'],
            package_use={'U13 six inverters':
                         'four state complements, U19 preterm, U15 output',
                         'U15 one S64 AOI': 'all four terms',
                         'U19 two of three triple NANDs':
                         'preterm and phase bit 1',
                         'U21 three of four NORs':
                         'mode inversion, NOR(mode,s6), tied-input NOR inverter'},
            unused_inputs='tied high; photographed electrical nets untraced'),
        observed_labels={'mode01': len(labels[0]),
                         'mode81_A1': len(labels[1]), 'errors': label_errors},
        saved_real_prom_replays=cases,
        limitations=[
            'This is a package-capacity circuit under explicit, untraced board connections; it does not identify U13/U15/U19/U21 actual nets.',
            'Saved real-PROM runs are replayed from captured states, not rerun here; the circuit was selected using the combined observed labels.',
            'Passing streams that contain only labeled states does not establish unseen-state or new carrier/gain transfer, nor a physical USART route.'
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    for case in result['saved_real_prom_replays']:
        print(case['source'], case['selector'], case['level'],
              case['errors'], len(case['unseen_states']))
