"""Inspect receive state and a frozen Boolean readout on joined Tx waveforms."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_mask04_full_zero_analog_variants import reconstructed_pcm
from joint_mask04_full_zero_handoff import ADC_VISITS, RX_CYCLES
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_phase47_logic import phase_quadrant
from reference_modem import QUADRANT_TO_DIBIT

PRIOR = HERE / 'results/joint-mask04-full-zero-handoff.json'
VARIANTS = HERE / 'results/joint-mask04-full-zero-analog-variants.json'
SELECTOR = '40'
CAPTURE_PHASE = 47
SYMBOLS = 64
VISITS_PER_SYMBOL = 375


def capture_state(mapping, base, pcm):
    samples = [127 - value for value in pcm]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC schedule changed')
    scenario = loopback.configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    row_visit = 0
    adc_visit = 0
    state = []
    rows = {}
    with tempfile.TemporaryDirectory() as temporary:
        result = loopback.execute(mapping, scenario, RX_CYCLES, mode='integrated',
                                  out=temporary, trace_limit=RX_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if row['pc'] == 0x3F8:
                if row['external_read']['value'] != values[adc_visit]:
                    raise ValueError('ADC read changed')
                adc_visit += 1
            elif row['pc'] == 0x3ED:
                visit, index = divmod(row_visit, 4)
                symbol, phase = divmod(visit, VISITS_PER_SYMBOL)
                if phase == CAPTURE_PHASE:
                    if index == 0:
                        rows[symbol] = dict(row0=row['alu']['y'])
                    elif index == 3:
                        rows[symbol]['row3'] = row['alu']['y']
                        state.append(dict(symbol=symbol, ram=ram[:], q=row['q'],
                                          row0=rows[symbol]['row0'],
                                          row3=rows[symbol]['row3']))
                row_visit += 1
    if (not result['clean'] or result['completed_cycles'] != RX_CYCLES or
            adc_visit != ADC_VISITS or row_visit != 4 * ADC_VISITS or
            len(state) != SYMBOLS):
        raise ValueError('receive state capture incomplete')
    return result, values, state


def boolean_decisions(state):
    phase = [phase_quadrant(row['row0'], row['row3']) for row in state]
    return [None] + [QUADRANT_TO_DIBIT[(phase[index] - phase[index - 1] - 2) & 3]
                     for index in range(1, len(phase))]


def run(out=HERE / 'results/joint-mask04-rx-state-level-probe.json'):
    prior = json.loads(PRIOR.read_text())
    variants = json.loads(VARIANTS.read_text())
    source = next(case for case in prior['cases'] if case['selector'] == SELECTOR)
    changed = next(case for case in variants['cases']
                   if case['selector'] == SELECTOR and
                   case['variant'] == 'gain_0p75_bias_plus16')
    pcm, offered, dibits, gain = reconstructed_pcm(source)
    expected = [3] * 32 + dibits
    mapping = loopback.candidate(loopback.mapping_with_upper_source(0, '17.6'),
                                 loopback.mapped(loopback.MAPPINGS['q3']), 4)
    _, base = loopback.fixture()
    cases = []
    for name, signal, saved in (
            ('nominal', pcm, source),
            ('gain_0p75_bias_plus16',
             [max(-127, min(127, round(value * 0.75 + 16))) for value in pcm],
             changed)):
        result, adc, state = capture_state(mapping, base, signal)
        if (result['trace_digest'] != saved['rx_trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() != saved['adc_sha256']):
            raise ValueError(('state probe differs from saved receiver run', name))
        decisions = boolean_decisions(state)
        wrong = [index for index in range(1, SYMBOLS)
                 if decisions[index] != expected[index]]
        cases.append(dict(name=name, rx_trace_digest=result['trace_digest'],
                          adc_sha256=saved['adc_sha256'],
                          boolean_wrong_symbols=wrong,
                          boolean_checks=SYMBOLS - 1,
                          states=state))
        print(name, 'Boolean errors', len(wrong), 'of', SYMBOLS - 1, flush=True)
    base_state, changed_state = (case['states'] for case in cases)
    summary = {}
    for index in range(16):
        original = [row['ram'][index] for row in base_state]
        varied = [row['ram'][index] for row in changed_state]
        summary[f'R{index}'] = dict(changed_symbols=sum(a != b for a, b in zip(original, varied)),
                                   nominal_distinct=len(set(original)),
                                   changed_distinct=len(set(varied)),
                                   nominal_first_8=original[:8], changed_first_8=varied[:8])
    original_q = [row['q'] for row in base_state]
    varied_q = [row['q'] for row in changed_state]
    summary['Q'] = dict(changed_symbols=sum(a != b for a, b in zip(original_q, varied_q)),
                        nominal_distinct=len(set(original_q)),
                        changed_distinct=len(set(varied_q)),
                        nominal_first_8=original_q[:8], changed_first_8=varied_q[:8])
    paths = (Path(__file__), PRIOR, VARIANTS,
             HERE / 'joint_mask04_full_zero_analog_variants.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             loopback.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='joined receive state under nominal and reduced-gain biased executed-Tx waveforms',
                  fixture=dict(selector=SELECTOR, offered_bytes=[f'{x:02X}' for x in offered],
                               nominal_pcm_gain=gain, capture_phase=CAPTURE_PHASE,
                               rx_cycles=RX_CYCLES,
                               changed_signal='0.75 times nominal PCM plus 16 counts',
                               readout='previously frozen phase-47 Boolean row0/row3 rule'),
                  cases=cases, state_change_summary=summary,
                  limitations=[
                      'A changed register value shows input sensitivity, not that it is a gain estimate or a physical decision output.',
                      'The Boolean rule was derived on reference waveforms; this executed-Tx challenge uses a different analog fixture and carrier phase.',
                      'DAC/ADC routes, latch timing and USART connections remain hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
