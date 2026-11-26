"""Test a labelled three-latch receiver candidate on saved real-PROM snapshots."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_row0_serial_timing as timing
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_row0_boolean import phase

HERE = Path(__file__).resolve().parent
SOURCES = (
    HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json',
    HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json',
)
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
OUT = HERE / 'results/joint-mask04-12a-row0-photo-latches.json'


def staged_state(symbol, variant):
    """Three independent, qualified captures; every value has its own storage."""
    visits = symbol['visits']
    u12_row_bit = visits[variant['row_visit']][variant['row_site']] & 1
    u14_first_y = (visits[variant['first_visit']]['y3f8'] >> 5) & 7
    second_y = visits[variant['second_visit']]['y3f8']
    u3_second_y = ((second_y >> 7) & 1) | (((second_y >> 4) & 1) << 1)
    u3_second_y |= ((second_y >> 6) & 1) << 2
    return u14_first_y | (u3_second_y << 3) | (u12_row_bit << 6)


def run(out=OUT):
    model = json.loads(LOGIC.read_text())
    covers = timing.covers_from_model(model)
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    if len(inverse) != 4:
        raise ValueError('phase convention must cover four steps')
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        for source in SOURCES:
            cases = json.loads(source.read_text())['cases']
            if len(cases) != (6 if source == SOURCES[0] else 2):
                raise ValueError('saved real-PROM case count changed')
            for case in cases:
                states = [staged_state(symbol, timing.VARIANTS['aligned'])
                          for symbol in case['multi_visit_symbols']]
                if len(states) != handoff.RX_SYMBOLS:
                    raise ValueError('symbol count changed')
                if any((phase(state, covers), state) !=
                       (observed_phase, observed_state)
                       for state, (observed_phase, _, observed_state) in
                       zip(states, (timing.captured_phase(symbol,
                              timing.VARIANTS['aligned'], covers)
                              for symbol in case['multi_visit_symbols']))):
                    raise ValueError('staged capture disagrees with existing replay')
                variants = {name: timing.replay(case, variant, covers, inverse, exe)
                            for name, variant in timing.VARIANTS.items()}
                aligned = variants['aligned']
                expected_payload = [int(value, 16) for value in case['payload']]
                if (aligned['wrong_decision_indices'] or aligned['unknown_rxc_edges'] or
                        not aligned['recovered_matches_offered'] or
                        aligned['controller_decoded_bytes'] != expected_payload or
                        aligned['controller_errors'] or aligned['controller_overruns'] or
                        aligned['minimum_setup_cycles'] != 2961):
                    raise ValueError(('candidate failed', source.name, case['selector']))
                if (variants['row_one_visit_late']['wrong_decision_indices'] or
                        not variants['rxc_before_second_capture']['unknown_rxc_edges'] or
                        not all(variants[name]['wrong_decision_indices'] for name in
                                ('row3_substitution', 'first_y_one_visit_late',
                                 'second_y_one_visit_late'))):
                    raise ValueError(('control changed', source.name, case['selector']))
                rows.append(dict(source=source.name, selector=case['selector'],
                                 level=case['level'], payload=case['payload'],
                                 rx_trace_digest=case['rx_trace_digest'],
                                 distinct_captured_states=len(set(states)),
                                 variants={name: dict(
                                     decision_errors=len(result['wrong_decision_indices']),
                                     unknown_rxc_edges=len(result['unknown_rxc_edges']),
                                     recovered_matches_offered=result['recovered_matches_offered'],
                                     controller_decoded_bytes=result['controller_decoded_bytes'],
                                     minimum_setup_cycles=result['minimum_setup_cycles'])
                                     for name, result in variants.items()}))
    paths = (Path(__file__), LOGIC, *SOURCES,
             HERE / 'joint_mask04_12a_row0_serial_timing.py')
    report = dict(
        experiment='photo-part capacity hypothesis for row/phase capture and serial output',
        fixture=dict(
            saved_real_prom_cases=len(rows), symbols_per_case=handoff.RX_SYMBOLS,
            phase_gates='frozen 22-state two-output Boolean model',
            assumed_capture_stages={
                'U12 SN74LS175N': 'one FF stores 3ED row-0 Y0 at visit 46',
                'U14 SN74LS75N': 'three latches store first 3F8 Y5,Y6,Y7 at visit 46',
                'U3 74LS373 PC': 'three latches store second 3F8 Y7,Y4,Y6 at visit 93',
                'U25 HD74LS74AP': 'candidate two FFs store previous phase bits',
                'U24 74LS161N': 'candidate row/visit qualification; not net-traced',
                'U28 74LS169AN': 'candidate symbol/bit selection; not net-traced',
            },
            first_rxc_cycle=timing.BIT_CYCLES,
            rxc_period_cycles=timing.BIT_CYCLES,
            assumed_syndet_bit=handoff.DATA_START_BIT,
            controller_probe_sha256=controller_sha),
        cases=rows,
        limitations=[
            'Chip assignments are capacity-compatible hypotheses, not traced pin connections or demonstrated simultaneous board use.',
            'Saved snapshots come from real-PROM execution, but capture gates and phase logic are external replay, not DSC instructions.',
            'No physical ADC, latch enables, RxD/RxC/SYNDET nets, or analog front-end timing has been measured.',
            'The first dibit and SYNDET edge are supplied by the known preamble fixture.',
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('cases', len(report['cases']))
    for row in report['cases']:
        print(row['source'], row['selector'], row['level'],
              {name: (value['decision_errors'], value['unknown_rxc_edges'])
               for name, value in row['variants'].items()})
