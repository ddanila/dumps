"""Test a one-cycle raw-PROM gate for the photo-compatible ADC buffers."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_3eb_adc_route_screen import CYCLES, VISITS, scenario

CHIPS = ('10', '11', '17', '18')
ADC_PC = 0x3F8


def predicate(raw):
    """Candidate active level: !U10.D1 & U10.D3 & U10.D7."""
    return not (raw[0] & 0x02) and bool(raw[0] & 0x08) and bool(raw[0] & 0x80)


def capture(mapping, candidate_scenario):
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, candidate_scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').open()]
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            result['address_counts'].get(ADC_PC, 0) != VISITS):
        raise ValueError('two-row ADC enable run stopped')
    return result, trace


def gate_counts(trace):
    same = Counter()
    delayed = Counter()
    entered = False
    previous = None
    transitions = {}
    for row in trace:
        pc = row['pc']
        entered |= pc == 0x3EA
        if entered:
            if predicate(row['raw']):
                same[pc] += 1
            if previous is not None:
                transitions[(previous['pc'], pc)] = previous['raw']
                if predicate(previous['raw']):
                    delayed[pc] += 1
        previous = row
    return same, delayed, transitions


def literal_vectors(transitions):
    """List every raw bit and its complement over reached loop transitions."""
    vectors = []
    pairs = list(transitions)
    for lane, chip in enumerate(CHIPS):
        for bit in range(8):
            for invert in (False, True):
                vectors.append((f'{"!" if invert else ""}{chip}.{bit}',
                                tuple(bool((transitions[pair][lane] >> bit) & 1) ^ invert
                                      for pair in pairs)))
    return pairs, vectors


def run(out=HERE / 'results/receiver-prom-adc-enable-phase.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    samples = codes((0, 1, 3, 2), 32, 'complementary')
    values = [value for sample, value in enumerate(samples)
              for _ in range(94 if sample % 4 < 3 else 93)]
    if len(values) != VISITS:
        raise ValueError('two-row ADC sample hold changed')
    baseline = scenario(base, False, True, values)
    base_result, base_trace = capture(mapping, baseline)
    same, delayed, transitions = gate_counts(base_trace)
    pairs, literals = literal_vectors(transitions)
    target = tuple(pc == ADC_PC for source, pc in pairs)
    single_count = sum(vector == target for name, vector in literals)
    pair_count = sum(tuple(a and b for a, b in zip(left, right)) == target
                     for i, (_, left) in enumerate(literals)
                     for _, right in literals[i + 1:])
    if (single_count or pair_count or
            {f'{pc:03X}': count for pc, count in same.items()} !=
            {'3F7': 3000} or
            {f'{pc:03X}': count for pc, count in delayed.items()} !=
            {'3F8': 3000}):
        raise ValueError('raw PROM gate timing changed')
    gated = scenario(base, False, False, values)
    # The site is derived from the one-cycle raw-PROM predicate, not named
    # as an ADC read in this scenario before the gate calculation.
    enabled_sites = sorted(delayed)
    if enabled_sites != [ADC_PC]:
        raise ValueError('PROM gate did not isolate ADC read site')
    for pc in enabled_sites:
        gated['io']['read']['pc_sequences'][str(pc)] = values
    gated['io']['read']['evidence'] += (
        '; receiver-window-qualified one-cycle LS244 enable hypothesis '
        '!U10.D1 & U10.D3 & U10.D7')
    gated_result, gated_trace = capture(mapping, gated)
    if gated_result['trace_digest'] != base_result['trace_digest']:
        raise ValueError('PROM-gated ADC changed the reached machine state')
    for row in gated_trace:
        if row['pc'] == ADC_PC and (not row['external_read']['selected_by_alu'] or
                                   row['external_read']['value'] != values[
                                       row['external_read']['visit']]):
            raise ValueError('gated 3F8 ADC byte changed')
    if not all(row['external_read']['selected_by_alu']
               for row in base_trace if row['pc'] == 0x3FA):
        raise ValueError('high-slice 3FA D selection changed')
    failed_pair = scenario(base, False, True, values)
    failed_pair['io']['read']['pc_sequences'][str(0x3FA)] = values
    failed_pair['io']['read']['evidence'] += (
        '; negative control for one-cycle !U10.D1 & U10.D3 gate '
        'that also enables high-slice D at 3FA')
    failed_result = execute(mapping, failed_pair, CYCLES,
                            mode='integrated', trace_limit=0)
    if (not failed_result['clean'] or
            failed_result['address_counts'].get(ADC_PC, 0) != 95 or
            failed_result['final_state']['pc'] != 0x084):
        raise ValueError('two-bit high-slice conflict changed')
    source_paths = (Path(__file__),
                    HERE / 'receiver_3eb_adc_route_screen.py',
                    HERE / 'receiver_3eb_nibble_truth.py',
                    HERE.parent / 'assumed/execute.py',
                    HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg',
                    *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='one-cycle raw-PROM ADC output-enable hypothesis',
                  fixture=dict(mapping='joint upper-source mask 08',
                               dispatch='scenario [0,2] at 3EC',
                               adc='32 complementary samples, 94/93 visits each',
                               buffer='photo-supported 74LS244 pair; connection untraced',
                               gate='!U10.D1 & U10.D3 & U10.D7, latched one microinstruction',
                               receiver_window='after first 3EA entry'),
                  same_phase_enabled_pcs={f'{pc:03X}': count
                                          for pc, count in sorted(same.items())},
                  delayed_enabled_pcs={f'{pc:03X}': count
                                       for pc, count in sorted(delayed.items())},
                  single_literal_gate_count=single_count,
                  two_literal_gate_count=pair_count,
                  baseline_trace_digest=base_result['trace_digest'],
                  gated_trace_digest=gated_result['trace_digest'],
                  failed_two_literal_control=dict(
                      predicate='!U10.D1 & U10.D3, one-cycle delay',
                      extra_selected_site='3FA high-slice D',
                      adc_visits=failed_result['address_counts'].get(ADC_PC, 0),
                      final_pc=f'{failed_result["final_state"]["pc"]:03X}',
                      trace_digest=failed_result['trace_digest']),
                  selected_adc_visits=VISITS,
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['same_phase_enabled_pcs'], result['delayed_enabled_pcs'])
