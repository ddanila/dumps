"""Audit frozen veto replays and distinguish active from inactive holdouts."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
GRAPH = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'
VETO = RESULTS / 'joint-mask04-12a-phasebit0-veto.json'
INPUTS = (
    ('phase137', RESULTS / 'joint-mask04-12a-phasebit0-veto-phase137-holdout.json'),
    ('phase139', RESULTS / 'joint-mask04-12a-phasebit0-veto-phase139-challenge.json'),
    ('phase131_115', RESULTS / 'joint-mask04-12a-phasebit0-veto-phase131-holdout.json'),
    ('phase131_125', RESULTS / 'joint-mask04-12a-phasebit0-veto-125gain-holdout.json'),
)
OUT = RESULTS / 'joint-mask04-12a-phasebit0-veto-holdout-audit.json'


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    graph = json.loads(GRAPH.read_text())
    veto = json.loads(VETO.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    known = {int(code, 16) for code in graph['combined_mode81_phase_labels']}
    if (veto['observed_labels']['errors'] or
            len(veto['saved_real_prom_replays']) != 22):
        raise ValueError('frozen veto development changed')
    cases = []
    for fixture, path in INPUTS:
        report = json.loads(path.read_text())
        for case in report['cases']:
            states = [sample_state(symbol, SELECTED)
                      for symbol in case['multi_visit_symbols']]
            original = [circuit(state, 1) for state in states]
            corrected = [corrected_phase(state, 1) for state in states]
            def wrong(phases):
                return [index for index in range(1, len(phases))
                        if inverse[(phases[index] - phases[index - 1]) & 3]
                        != case['expected_dibits'][index]]
            original_wrong = wrong(original)
            corrected_wrong = wrong(corrected)
            crossings = [index for index in range(1, len(states))
                         if ((states[index - 1] in (0x2F, 0x48)) !=
                             (states[index] in (0x2F, 0x48)))]
            score = case['corrected_serial']
            payload = [int(value, 16) for value in case['payload']]
            active = bool(crossings)
            if (len(states) != 65 or set(states) - known or
                    original_wrong != crossings or corrected_wrong or
                    case['corrected_wrong_indices'] or
                    case['unseen_vs_20_labels'] or
                    score['wrong_decision_indices'] or
                    score['unknown_rxc_edges'] or
                    not score['recovered_matches_offered'] or
                    score['controller_decoded_bytes'] != payload or
                    score['controller_errors'] or score['controller_overruns'] or
                    score['minimum_setup_cycles'] != 2961 or
                    (fixture in ('phase137', 'phase139') and active) or
                    (fixture in ('phase131_115', 'phase131_125') and not active)):
                raise ValueError(('veto holdout audit failed', fixture,
                                  case['selector']))
            cases.append(dict(fixture=fixture, selector=case['selector'],
                              carrier_offset=report['fixture']['R1_offset'],
                              gain_factor=report['fixture']['gain_factor'],
                              veto_exercised=active,
                              original_circuit_errors=len(original_wrong),
                              corrected_errors=0,
                              reference_errors=len(case['reference_wrong_indices']),
                              clipped_samples=case['clipped_samples'],
                              unseen_states=0, exact_line_bytes=True,
                              exact_controller_bytes=True))
    if (len(cases) != 8 or
            [case['original_circuit_errors'] for case in cases] !=
            [0, 0, 0, 0, 17, 12, 15, 17] or
            [case['clipped_samples'] for case in cases] !=
            [0, 0, 0, 0, 0, 0, 4, 2]):
        raise ValueError('veto holdout case coverage changed')
    paths = (Path(__file__), MODEL, GRAPH, VETO,
             *(path for _, path in INPUTS),
             HERE / 'joint_mask04_12a_phasebit0_veto.py')
    report = dict(experiment='frozen two-term phase-bit-0 veto holdout audit',
                  cases=cases,
                  active_veto_cases=4,
                  inactive_transfer_cases=4,
                  limitations=[
                      'The active holdouts use fresh payloads at the already-failing phase-131 gain fixtures; no previously unseen state appears.',
                      'The phase-137 and phase-139 runs transfer to new carrier/payloads but never exercise the veto terms.',
                      'The two-term correction remains an assumed external circuit with no assigned photographed package or physical serial nets.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(run()['cases'])
