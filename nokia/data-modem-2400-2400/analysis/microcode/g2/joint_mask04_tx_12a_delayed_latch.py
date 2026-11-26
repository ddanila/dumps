"""Run the PROM-decode DAC clock with two explicit gate/Y delay orders."""

import hashlib
import json
from pathlib import Path

from joint_mask04_tx_bank_phase import (EXECUTE, scenario_for)
from joint_four_row_retention_tx import (BUSES, MAPPINGS, SAMPLE_COUNT,
                                         SAMPLE_DIVISOR, TXREADY, candidate,
                                         fixture, mapped,
                                         mapping_with_upper_source)
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import bandpass
from photo_joint_tone_training_data import (SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_SYMBOLS,
                                            TOTAL_SYMBOLS, segment2_from_txd)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from reference_modem import spectral_peak

HERE = Path(__file__).resolve().parent
GATE_REPORT = HERE / 'results/joint-mask04-tx-12a-gate.json'
PRIOR = HERE / 'results/joint-mask04-tx-bank-phase.json'
SITES = (0x127, 0x12A)


def capturing_execute(phase_poke=None):
    source = EXECUTE.read_text()
    patches = (
        ("    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0",
         "    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0\n"
         "    site_y={0x127:[],0x12A:[]}"),
        ("            carry_input.observe(result)",
         "            if pc in site_y:site_y[pc].append(result['y'])\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['site_y']=site_y\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection point moved', old))
        source = source.replace(old, new)
    if phase_poke is not None:
        visit, offset = phase_poke
        if visit < 1 or not 0 <= offset <= 255:
            raise ValueError('invalid phase poke')
        old = "            carry=carry_input.resolve(r)"
        new = ("            if pc==0x127 and sequence_visits[0x127]=="
               f"{visit}:cpu.ram[1]=(cpu.ram[1]+{offset})&255\n" + old)
        if source.count(old) != 1:
            raise ValueError('phase poke injection point moved')
        source = source.replace(old, new)
    scope = {'__name__': 'joint_mask04_tx_12a_delay_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def score(raw, buses, symbols):
    tone_end = TONE_SYMBOLS * 8
    silence_end = (TONE_SYMBOLS + SILENCE_SYMBOLS) * 8
    scored = []
    for bus in buses:
        codes = mapped_codes(raw, bus)
        tone = spectral_peak([code - 128 for code in codes[64:tone_end]],
                             lower=100, upper=3500)
        muted = codes[:tone_end] + [128] * (silence_end - tone_end) + codes[silence_end:]
        line = bandpass([code - 128 for code in muted], 1.0)
        decoded = decision_result([value + 128 for value in line[silence_end:]],
                                  symbols, sample_shift=6)
        if decoded['decisions'] != 62:
            raise ValueError('A3/A4 decision count changed')
        scored.append(dict(tone_peak_hz=tone['frequency_hz'],
                           filtered_data_errors=decoded['errors'],
                           code_sha256=hashlib.sha256(bytes(codes)).hexdigest()))
    return scored


def run(out=HERE / 'results/joint-mask04-tx-12a-delayed-latch.json'):
    execute = capturing_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    controller = json.loads(TXREADY.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    gate = json.loads(GATE_REPORT.read_text())
    prior = json.loads(PRIOR.read_text())
    if len(buses) != 6 or len(gate['full']) != 2:
        raise ValueError('photo-compatible fixture changed')
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    cases = []
    for selector in ('40', '60'):
        controller_case = next(case for case in controller['cases']
                               if case['selector'] == selector)
        symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(controller_case)
        bank_runs = {}
        for bank in (256, 0):
            result = execute(mapping, scenario_for(base, controller_case, bank),
                             cycles, mode='integrated', trace_limit=0)
            site_y = result['site_y']
            if (not result['clean'] or result['completed_cycles'] != cycles or
                    result['address_counts'].get(0x12A) != 312054 or
                    len(site_y[0x12A]) != 312054 or
                    len(site_y[0x127]) != 312054):
                raise ValueError(('TX replay changed', selector, bank,
                                  len(site_y[0x127]), len(site_y[0x12A])))
            early = [site_y[0x12A][SAMPLE_DIVISOR * n]
                     for n in range(SAMPLE_COUNT)]
            late = [site_y[0x127][SAMPLE_DIVISOR * n + 1]
                    for n in range(SAMPLE_COUNT)]
            bank_runs[bank] = dict(trace_digest=result['trace_digest'],
                                   early=early, late=late)
        prior_case = next(case for case in prior['cases']
                          if case['selector'] == selector)
        gate_case = next(case for case in gate['full']
                         if case['selector'] == selector)
        for bank in (256, 0):
            if bank_runs[bank]['trace_digest'] != prior_case['trace_digests'][str(bank)]:
                raise ValueError(('full bank-phase trace changed', selector, bank))
        if bank_runs[256]['trace_digest'] != gate_case['trace_digest']:
            raise ValueError('PROM gate and latch trace differ')
        phases = []
        for phase in ('early', 'late'):
            a, b = bank_runs[256][phase], bank_runs[0][phase]
            masks = {f'{mask:02X}': sum((x ^ y) == mask for x, y in zip(a, b))
                     for mask in sorted({x ^ y for x, y in zip(a, b)} - {0})}
            phases.append(dict(timing=phase,
                               bank_changed_samples=sum(x != y for x, y in zip(a, b)),
                               bank_xor_masks=masks,
                               banks={str(bank): dict(raw_y_sha256=hashlib.sha256(bytes(
                                   bank_runs[bank][phase])).hexdigest(),
                                   bus_scores=score(bank_runs[bank][phase], buses,
                                                    symbols)) for bank in (256, 0)}))
        prior_12a = next(site for site in prior_case['sites'] if site['pc'] == '12A')
        if phases[0]['bank_changed_samples'] != prior_12a['sample_cases'][0]['changed_y_samples']:
            raise ValueError('qualified early-latch sample count changed')
        cases.append(dict(selector=selector, trace_digests={str(bank):
                          bank_runs[bank]['trace_digest'] for bank in (256, 0)},
                          sample_count=SAMPLE_COUNT, divisor=SAMPLE_DIVISOR,
                          phases=phases))
    paths = (Path(__file__), EXECUTE, GATE_REPORT, PRIOR, TXREADY, BUSES,
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='counter-qualified 12A PROM-edge DAC data timing',
                  fixture=dict(edge='U11.D0 & U17.D1 falls at 12A->127; NAND rises',
                               counter_divisor=SAMPLE_DIVISOR,
                               early='PROM gate clocks before new 127 ALU Y settles: latch previous 12A Y',
                               late='new 127 ALU Y settles before clock: latch 127 Y',
                               dac_buses='six photo-compatible survivors',
                               analog='A2 mid-code mute and assumed bandpass'),
                  cases=cases,
                  limitations=[
                      'The counter, gate polarity, relative propagation delays, LS273 clock/data nets and DAC pins are assumed.',
                      'The externally filtered line and decoder are diagnostics, not measured analog output.',
                      'A full-trace PC-gate census was established separately; these runs capture Y at the two adjacent PCs.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
