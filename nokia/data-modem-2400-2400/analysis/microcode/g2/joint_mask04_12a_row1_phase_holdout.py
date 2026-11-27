"""Challenge a frozen row-0 Y1 phase lookup on fresh PROM streams."""

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
GRAPH = RESULTS / 'joint-mask04-12a-0d-feature-graph.json'
BASE_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
GAIN = RESULTS / 'joint-mask04-12a-row1-phase-gain075-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-row1-phase-holdout.json'
FACTOR = 0.75
FIXTURES = (
    (141, {'40': (0x6A, 0xC1, 0x37, 0xE8, 0x04, 0xBD, 0x92, 0x5F),
           '60': (0xB3, 0x0E, 0xD5, 0x49, 0xF7, 0x21, 0x8C, 0x6A)}),
    (143, {'40': (0xF1, 0x28, 0x9D, 0x43, 0xBA, 0x06, 0x75, 0xCE),
           '60': (0x4D, 0xE2, 0x17, 0xA9, 0x50, 0xCB, 0x36, 0x8F)}),
)


def make_gain_fixture():
    base = json.loads(BASE_GAIN.read_text())
    fixture = dict(experiment='frozen 0.75x bus-0 receive gain fixture',
                   source_file=BASE_GAIN.name,
                   source_sha256=hashlib.sha256(BASE_GAIN.read_bytes()).hexdigest(),
                   gain_factor=FACTOR,
                   cases=[dict(selector=case['selector'], bus_cases=[
                       dict(bus_index=0, gain=next(bus['gain'] for bus in
                           case['bus_cases'] if bus['bus_index'] == 0) * FACTOR)])
                       for case in base['cases']])
    GAIN.write_text(json.dumps(fixture, indent=2) + '\n')


def state_key(symbol):
    return sample_state(symbol, SELECTED) | \
        (((symbol['visits']['46']['row0'] >> 1) & 1) << 7)


def run(out=OUT):
    make_gain_fixture()
    graph = json.loads(GRAPH.read_text())
    selected = graph['results']['row0_bit1']
    if (selected['state_codes'] != 24 or
            selected['directed_conflicts'] != 0 or
            selected['components'] != [24]):
        raise ValueError('frozen row-0 bit-1 graph changed')
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
            return phase_map[key], serial.Y3F8_CYCLE + 93 * serial.CYCLES_PER_VISIT, key
        for offset, payloads in FIXTURES:
            path = RESULTS / f'joint-mask04-12a-row1-phase-holdout-{offset}.json'
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
                print('row1 holdout', offset, selector,
                      'unseen', rows[-1]['unseen_keys'],
                      'known errors', len(known_wrong),
                      'complete errors', (len(score['wrong_decision_indices'])
                                          if score else 'unclassified'), flush=True)
    paths = (Path(__file__), GRAPH, BASE_GAIN, GAIN,
             Path(challenge.__file__), Path(edge.__file__),
             *(path for path in expanded))
    report = dict(experiment='frozen row-0 Y1 phase graph on fresh controller streams',
                  fixture=dict(payloads={str(offset): {selector: [f'{value:02X}'
                      for value in payload] for selector, payload in payloads.items()}
                      for offset, payloads in FIXTURES},
                               carrier_offsets=[offset for offset, _ in FIXTURES],
                               gain_factor=FACTOR,
                               state='seven captured bits plus row-0 Y1 at visit 46',
                               phase_table_codes=len(phase_map),
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The phase table is frozen from the 18 development streams; an unseen key is unclassified, not assigned a guessed phase.',
                      'The eight-bit table is a graph lookup, not a Boolean gate or identified Nokia logic.',
                      'DAC/line, ADC, latch, controller mode, RxD/RxC and SYNDET connections remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
