"""Compare direct/inverted real U10 data bits as candidate U5 Q0 sources."""

import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
import execute as executor
from common import read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import CONTROLLER, live_dispatch
from photo_table_controller_source import table_output_flow
from photo_table_exact_transform import expected
from photo_table_phase_consumer import SEEDS, in_table
from photo_table_prombit_consumer import BASE_DECODE
from photo_table_restart_dibits import trace_run


def candidate_decode(bit, inverted):
    def decode(mapping, lanes):
        rows = BASE_DECODE(mapping, lanes)
        for pc, row in enumerate(rows):
            level = ((lanes['10'][pc] >> bit) & 1) ^ inverted
            row['i'] = (row['i'] & ~1) | level
            row['a'] = (row['a'] & ~2) | (level << 1)
        return rows
    return decode


def candidate_scenario(bit, inverted, line_bytes):
    state = live_dispatch(scenario_for(1, 0))
    state['name'] = state['name'].replace(
        'E2=0', f'I0/A1 from U10 bit {bit}, inverted={inverted}; U10 E2 held low')
    del state['inputs']['instruction_bit_overrides']['0']
    del state['inputs']['register_address_bit_overrides']['a']['1']
    state['io']['read'].update(
        mode='pc_sequence', value=0, sequence_end='hold-last',
        status='hypothesis',
        evidence='Actual 8031 USART-01 bytes offered at candidate D349; input route and timing untraced',
        pc_sequences={str(0x349): line_bytes})
    return state


def run(out=HERE / 'results/photo-u10-q0-source-screen.json'):
    controller = read(CONTROLLER)
    group = next(x for x in controller['groups'] if x['selectors'][0] == '20')
    line_bytes = group['line_bytes']
    mapping = mapped(MAPPINGS['q3'])
    candidates = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for bit in range(8):
            for inverted in (0, 1):
                runs = []
                with patch.object(executor, 'decode', candidate_decode(bit, inverted)):
                    for seed in SEEDS:
                        state = candidate_scenario(bit, inverted, line_bytes)
                        result, trace, restarts = trace_run(
                            mapping, state, seed, directory)
                        calls = reached_calls(trace, state)
                        flow = table_output_flow(trace)
                        outside = [event for event in flow['downstream_reads']
                                   if not in_table(int(event['pc'], 16))]
                        internal = [trace[event['cycle']]['alu']['y']
                                    for event in outside
                                    if event['pc'] in ('140', '146')]
                        output = [row['alu']['y'] for row in trace
                                  if row['pc'] in (0x392, 0x39E)]
                        if len(restarts) != 15 or not calls:
                            raise ValueError('screen fixture lost restart or table path')
                        runs.append(dict(seed=seed, calls=len(calls),
                                         sign_formula_matches=sum(
                                             tuple(call['output_after']) ==
                                             expected(call['source'], call['entry'])
                                             for call in calls),
                                         downstream_table_reads=len(outside),
                                         nonzero_internal_consumers=sum(bool(x)
                                                                        for x in internal),
                                         output_candidate_y=sorted(set(output)),
                                         trace_digest=result['trace_digest']))
                candidates.append(dict(bit=bit, inverted=bool(inverted),
                                       runs=runs,
                                       total_calls=sum(x['calls'] for x in runs),
                                       sign_formula_matches=sum(
                                           x['sign_formula_matches'] for x in runs),
                                       downstream_table_reads=sum(
                                           x['downstream_table_reads'] for x in runs),
                                       nonzero_internal_consumers=sum(
                                           x['nonzero_internal_consumers'] for x in runs)))
    winners = [x for x in candidates if
               x['sign_formula_matches'] == x['total_calls'] and
               x['downstream_table_reads'] > 0 and
               x['nonzero_internal_consumers'] > 0]
    if (len(candidates) != 16 or len(winners) != 1 or
            (winners[0]['bit'], winners[0]['inverted']) != (5, True) or
            any(x['total_calls'] != 33 for x in candidates)):
        raise ValueError('U10 candidate separation changed')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_prombit_consumer.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_controller_source.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_table_phase_consumer.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='diagnostic candidate U10 data source ranking',
                  fixture=dict(mapping='q3', seeds=list(SEEDS), cycles=2500,
                               controller_selector='20', line_bytes=line_bytes,
                               d349='successive controller bytes',
                               candidate_u5_d0='U10 data bit 0..7, direct or inverted',
                               candidate_u5_q0='Am2901 I0 and A1, per decoded microaddress',
                               u10_e2='held low for valid PROM data',
                               e4_i7_a0=1, diagnostic_rst_pulses=15,
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  candidates=candidates,
                  unique_joint_winner=dict(bit=winners[0]['bit'],
                                           inverted=winners[0]['inverted'],
                                           calls=winners[0]['total_calls'],
                                           formula_matches=winners[0]['sign_formula_matches'],
                                           downstream_reads=winners[0]['downstream_table_reads'],
                                           nonzero_consumers=winners[0]['nonzero_internal_consumers']),
                  limitations=[
                      'This ranks only eight U10 data bits and polarities in four diagnostic branch fixtures, not all possible board sources.',
                      'The inverted bit-5 route requires an untraced inversion or different dump convention; neither is established by the 6381 pinout.',
                      'Per-word U5 capture, U5 Q0 fan-out, D349 controller route, previous-Y branch bus and AC=RST override are hypotheses.',
                      'Formula and internal-consumer behavior are not a DAC waveform or a receiver/echo demonstration.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['unique_joint_winner'])
