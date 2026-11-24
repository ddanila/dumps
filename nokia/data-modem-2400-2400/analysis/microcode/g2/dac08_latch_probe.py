"""Replay real-PROM paths through a hypothetical LS273→DAC08 digital output."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture

Q1_MAPPING = HERE/'results/photo-variant-rom-loop/q1-witness-mapping.json'
Q1_SCENARIO = HERE/'results/photo-variant-rom-loop/q1-witness-scenario.json'
FITTED_MAPPING = ASSUMED/'results/selector-completion/swapped-marked/mapping.json'


class LS273DAC08:
    """Digital-only latch: Q is unknown until clear or a rising capture edge."""
    def __init__(self):
        self.q = None
        self.clock = 0

    def drive(self, data, clock, clear_n=1):
        if data is not None and (type(data) is not int or not 0 <= data <= 255):
            raise ValueError('LS273 input must be a byte or unknown')
        if clock not in (0, 1) or clear_n not in (0, 1):
            raise ValueError('LS273 controls must be binary')
        if not clear_n:
            self.q = 0
        elif self.clock == 0 and clock == 1:
            self.q = data
        self.clock = clock
        return self.q


class LS373:
    """Digital latch: transparent while LE is high, held while LE is low."""
    def __init__(self):
        self.q = None

    def drive(self, data, le):
        if data is not None and (type(data) is not int or not 0 <= data <= 255):
            raise ValueError('LS373 input must be a byte or unknown')
        if le not in (0, 1):
            raise ValueError('LS373 LE must be binary')
        if le:
            self.q = data
        return self.q


def capture(trace, pc):
    latch = LS273DAC08()
    codes = []
    for row in trace:
        data = row['alu']['y']
        if row['pc'] == pc:
            code = latch.drive(data, 1)
            codes.append(dict(cycle=row['cycle'], pc=f'{pc:03X}', latch_q=code))
            latch.drive(data, 0)
        else:
            latch.drive(data, 0)
    return codes


def staged_capture(trace):
    """Hypothetical 38E→LS373 hold→LS273 edge at 392 or 39E."""
    upstream = LS373()
    output = LS273DAC08()
    captures = []
    bit = None
    for row in trace:
        if row['pc'] == 0x38E:
            bit = row['external_read']['value']
            upstream.drive(row['alu']['y'], 1)
            upstream.drive(None, 0)
        if row['pc'] in (0x392, 0x39E):
            code = output.drive(upstream.q, 1)
            captures.append(dict(cycle=row['cycle'], pc=f"{row['pc']:03X}",
                                 controller_bit=bit, latch_q=code))
            output.drive(upstream.q, 0)
    return captures


def execute_trace(mapping, scenario, cycles):
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != cycles:
        raise ValueError('DSP execution incomplete')
    return result, trace


def run(out):
    latch_check = LS273DAC08()
    assert latch_check.drive(0x12, 0) is None
    assert latch_check.drive(0x34, 1) == 0x34
    assert latch_check.drive(0x56, 1) == 0x34
    assert latch_check.drive(0x78, 0) == 0x34
    assert latch_check.drive(0x9A, 1) == 0x9A
    assert latch_check.drive(0xBC, 1, clear_n=0) == 0
    stage_check = LS373()
    assert stage_check.drive(0x12, 0) is None
    assert stage_check.drive(0x34, 1) == 0x34
    assert stage_check.drive(0x56, 0) == 0x34

    q1_result, q1_trace = execute_trace(read(Q1_MAPPING), read(Q1_SCENARIO), 2048)
    q1_codes = capture(q1_trace, 0x12C)
    if len(q1_codes) != 500:
        raise ValueError('q1 ROM-loop capture count changed')

    q3_mapping, q3_scenario = fixture()
    _, bits = controller_stream()
    q3_scenario['initial']['q'] = 5
    q3_scenario['io']['read']['pc_sequences']['910'] = bits
    q3_result, q3_trace = execute_trace(q3_mapping, q3_scenario, 1580)
    if [row['external_read']['value'] for row in q3_trace if row['pc'] == 0x38E] != bits:
        raise ValueError('q3 controller stream not consumed')
    q3_codes = capture(q3_trace, 0x392)
    if len(q3_codes) != 57 or set(row['latch_q'] for row in q3_codes) != {11}:
        raise ValueError('q3 output candidate changed')
    q3_staged = staged_capture(q3_trace)
    if (len(q3_staged) != len(bits) or
            [row['controller_bit'] for row in q3_staged] != bits or
            {bit: {row['latch_q'] for row in q3_staged
                   if row['controller_bit'] == bit} for bit in (0, 1)}
            != {0: {251}, 1: {252}}):
        raise ValueError('q3 staged latch result changed')

    fitted_mapping = read(FITTED_MAPPING)
    fitted_mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
    fitted_scenario = copy.deepcopy(q3_scenario)
    fitted_result, fitted_trace = execute_trace(fitted_mapping, fitted_scenario, 1580)
    if [row['external_read']['value'] for row in fitted_trace if row['pc'] == 0x38E] != bits:
        raise ValueError('fitted controller stream not consumed')
    fitted_codes = capture(fitted_trace, 0x396)
    if len(fitted_codes) != 128 or set(row['latch_q'] for row in fitted_codes) != {1}:
        raise ValueError('fitted output candidate changed')

    cases = []
    for name, pc, result, codes, controller_bits in (
            ('q1_rom_loop', 0x12C, q1_result, q1_codes, 0),
            ('q3_controller', 0x392, q3_result, q3_codes, len(bits)),
            ('fitted_controller', 0x396, fitted_result, fitted_codes, len(bits))):
        values = [row['latch_q'] for row in codes]
        cases.append(dict(name=name, hypothetical_clock_pc=f'{pc:03X}',
                          captures=len(codes), distinct_latch_codes=sorted(set(values)),
                          first_24_codes=values[:24], last_40_codes=values[-40:],
                          controller_bits_consumed=controller_bits,
                          trace_digest=result['trace_digest']))
    if len(set(cases[0]['last_40_codes'][:20])) != 20 or cases[0]['last_40_codes'][:20] != cases[0]['last_40_codes'][20:]:
        raise ValueError('q1 20-code recurrence changed')
    paths = [Path(__file__), Q1_MAPPING, Q1_SCENARIO, FITTED_MAPPING,
             HERE/'photo_controller_path.py', HERE/'controller_bit_dispatch.py',
             HERE/'results/swapped-sine-loop/phase-20-scenario.json',
             ASSUMED/'execute.py', HERE.parent/'model.py']
    report = dict(status='hypothetical DAC08 input replay, not physical output',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths},
                  model='LS273 holds unknown until a positive edge; sampled byte becomes candidate DAC08 B1–B8 identity code.',
                  cases=cases,
                  staged_q3=dict(hypothesis='ALU Y at 38E passes through transparent LS373, then is held until LS273 clock at branch output 392 or 39E',
                                 captures=len(q3_staged),
                                 controller_bits_consumed=len(bits),
                                 code_by_bit={str(bit): sorted({row['latch_q'] for row in q3_staged
                                                                if row['controller_bit'] == bit})
                                              for bit in (0, 1)},
                                 clock_sites={site: sum(row['pc'] == site for row in q3_staged)
                                              for site in ('392', '39E')},
                                 first_24_codes=[row['latch_q'] for row in q3_staged[:24]]),
                  limitations=['Clock-at-PC and LS273 Q1..Q8 to DAC08 B1..B8 identity are explicit untraced hypotheses.',
                               'The LS373 staging, its input/enable, and the two-site LS273 clock decode are untraced hypotheses.',
                               'q1 has a changing 20-code loop but no controller bits, phase increment or demonstrated output route.',
                               'The two controller-driven paths produce held codes and cannot demonstrate a carrier.',
                               'No analog current, filter, sample rate or line connection is modeled.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/dac08-latch-probe.json')
    print([(case['name'], case['captures'], len(case['distinct_latch_codes']))
           for case in report['cases']])
