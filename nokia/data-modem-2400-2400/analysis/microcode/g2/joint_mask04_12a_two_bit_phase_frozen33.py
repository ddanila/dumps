"""Challenge the 33-code row-0 Y1 plus later Y4 phase lookup."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_lowgain133_challenge as challenge
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GRAPH = RESULTS / 'joint-mask04-12a-two-bit-phase-extension.json'
GAIN = RESULTS / 'joint-mask04-12a-row1-phase-gain075-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-two-bit-phase-frozen33.json'
FACTOR = 0.75
FIXTURES = (
    (149, {'40': (0xD1, 0x4B, 0xA8, 0x36, 0xF0, 0x29, 0x85, 0x7C),
           '60': (0x63, 0xBE, 0x14, 0xC9, 0x52, 0x8F, 0xD0, 0x37)}),
    (151, {'40': (0x35, 0xE7, 0x90, 0x4C, 0xB2, 0x1A, 0x6D, 0xF8),
           '60': (0xA4, 0x09, 0x76, 0xCB, 0x51, 0xE2, 0x3F, 0x88)}),
)


def state_key(symbol):
    return sample_state(symbol, SELECTED) | \
        (((symbol['visits']['46']['row0'] >> 1) & 1) << 7) | \
        (((symbol['visits']['94']['y3f8'] >> 4) & 1) << 8)


def run(out=OUT):
    graph = json.loads(GRAPH.read_text())
    selected = graph['phase_graph']
    if (selected['state_codes'] != 33 or
            selected['directed_conflicts'] != 0 or
            selected['components'] != [33]):
        raise ValueError('frozen two-bit graph changed')
    phase_map = {int(code, 16): value for code, value in
                 selected['relative_phase'].items()}
    steps = graph['fixture']['phase_convention']
    inverse = {step: dibit for dibit, step in enumerate(steps)}
    rows = []
    expanded = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        def captured(symbol, variant, covers):
            key = state_key(symbol)
            return phase_map[key], serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, key
        for offset, payloads in FIXTURES:
            path = RESULTS / f'joint-mask04-12a-two-bit-phase-frozen33-{offset}.json'
            expanded.append(path)
            with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
                    patch.object(challenge, 'GAIN', GAIN), \
                    patch.object(challenge, 'FACTOR', FACTOR), \
                    patch.object(challenge, 'OFFSET', offset), \
                    patch.object(challenge, 'PAYLOADS', payloads):
                saved = challenge.run(out=path)
            if saved['fixture']['controller_probe_sha256'] != controller_sha:
                raise ValueError('controller probe changed')
            for case in saved['cases']:
                selector = case['selector']
                symbols = case['multi_visit_symbols']
                keys = [state_key(symbol) for symbol in symbols]
                unseen = sorted(set(keys) - set(phase_map))
                known_wrong = [index for index in range(1, len(keys))
                               if keys[index - 1] in phase_map and
                               keys[index] in phase_map and
                               inverse[(phase_map[keys[index]] -
                                        phase_map[keys[index - 1]]) & 3]
                               != case['expected_dibits'][index]]
                score = None
                if not unseen:
                    payload = list(payloads[selector])
                    offered = line_octets(payload, 5 if selector == '40' else 18)
                    with patch.object(serial, 'captured_phase', captured):
                        score = serial.replay(dict(case, offered_line_bytes=[
                            f'{value:02X}' for value in offered]),
                            serial.VARIANTS['aligned'], None, inverse, exe)
                    if known_wrong != score['wrong_decision_indices']:
                        raise ValueError('lookup and serial decisions differ')
                rows.append(dict(carrier_offset=offset, selector=selector,
                                 payload=[f'{value:02X}' for value in payloads[selector]],
                                 gain_factor=FACTOR,
                                 tx_trace_digest=case['tx_trace_digest'],
                                 rx_trace_digest=case['rx_trace_digest'],
                                 pcm_sha256=case['pcm_sha256'],
                                 clipped_samples=case['clipped_samples'],
                                 captured_keys=[f'{key:03X}' for key in keys],
                                 unseen_keys=[f'{key:03X}' for key in unseen],
                                 known_transition_wrong_indices=known_wrong,
                                 old_veto_errors=len(case['corrected_wrong_indices']),
                                 decoded_wrong_indices=(score['wrong_decision_indices']
                                                        if score else None),
                                 recovered_matches_offered=(score['recovered_matches_offered']
                                                            if score else None),
                                 controller_decoded_bytes=(score['controller_decoded_bytes']
                                                           if score else None),
                                 controller_errors=(score['controller_errors']
                                                    if score else None),
                                 minimum_setup_cycles=(score['minimum_setup_cycles']
                                                       if score else None)))
                print('frozen33 holdout', offset, selector,
                      'unseen', rows[-1]['unseen_keys'],
                      'known errors', len(known_wrong),
                      'complete errors', (len(score['wrong_decision_indices'])
                                          if score else 'unclassified'), flush=True)
    paths = (Path(__file__), GRAPH, GAIN,
             Path(challenge.__file__), Path(edge.__file__),
             *(path for path in expanded))
    report = dict(experiment='frozen 33-code row-0 Y1 plus later Y4 phase graph on fresh controller streams',
                  fixture=dict(payloads={str(offset): {selector: [f'{value:02X}'
                      for value in payload] for selector, payload in payloads.items()}
                      for offset, payloads in FIXTURES},
                               carrier_offsets=[offset for offset, _ in FIXTURES],
                               gain_factor=FACTOR,
                               state='seven captured bits plus row-0 Y1 at visit 46 and 3F8 Y4 at visit 94',
                               phase_table_codes=len(phase_map),
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The phase table is frozen from 26 development streams; an unseen key is unclassified, not assigned a guessed phase.',
                      'The nine-bit table is a graph lookup, not a Boolean gate or identified Nokia logic.',
                      'DAC/line, ADC, latch, controller mode, RxD/RxC and SYNDET connections remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
