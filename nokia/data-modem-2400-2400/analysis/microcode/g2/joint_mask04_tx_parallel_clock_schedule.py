"""Execute a whole-store 12A clock and parallel-latch OE schedule."""

import hashlib
import json
from pathlib import Path

from joint_mask04_tx_bank_phase import EXECUTE, scenario_for
from joint_four_row_retention_tx import (
    MAPPINGS, SAMPLE_COUNT, SAMPLE_DIVISOR, TXREADY, candidate, fixture,
    mapped, mapping_with_upper_source,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_joint_tone_training_data import TOTAL_SYMBOLS

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
PROM_DIR = HERE.parents[2] / 'microcode-810237c-810240c'
GATE = RESULTS / 'joint-mask04-tx-12a-full-store-gate.json'
PRIOR = RESULTS / 'joint-mask04-tx-12a-delayed-latch.json'
PARALLEL = RESULTS / 'joint-mask04-tx-parallel-latch-bus.json'
OUT = RESULTS / 'joint-mask04-tx-parallel-clock-schedule.json'
LITERALS = ((1, 0, 1), (2, 1, 1), (2, 3, 1), (3, 1, 0))


def instrument(observer):
    source = EXECUTE.read_text()
    old = '            carry_input.observe(result)'
    new = old + "\n            latch_observe(pc,result['y'],cycle)"
    if source.count(old) != 1:
        raise ValueError('executor observer injection point changed')
    scope = {'__name__': 'parallel_clock_schedule_instrumented',
             '__file__': str(EXECUTE), 'latch_observe': observer}
    exec(compile(source.replace(old, new), str(EXECUTE), 'exec'), scope)
    return scope['execute']


def run(out=OUT):
    rom_paths = sorted(PROM_DIR.glob('chip*.bin'))
    roms = [path.read_bytes() for path in rom_paths]
    if len(roms) != 4 or any(len(rom) != 1024 for rom in roms):
        raise ValueError('PROM files changed')

    def selected(pc):
        return all(((roms[chip][pc] >> bit) & 1) == value
                   for chip, bit, value in LITERALS)

    if [pc for pc in range(1024) if selected(pc)] != [0x12A]:
        raise ValueError('whole-store 12A decode changed')
    gate = json.loads(GATE.read_text())
    if {tuple(row) for row in gate['four_literal']['literals']} != set(LITERALS):
        raise ValueError('saved four-literal gate changed')
    prior = json.loads(PRIOR.read_text())
    parallel = json.loads(PARALLEL.read_text())
    controller = json.loads(TXREADY.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    cases = []
    for selector in ('40', '60'):
        controller_case = next(row for row in controller['cases']
                               if row['selector'] == selector)
        saved = next(row for row in prior['cases'] if row['selector'] == selector)
        old_parallel = next(row for row in parallel['cases']
                            if row['selector'] == selector)
        state = dict(previous_pc=None, previous_y=None, previous_cycle=None,
                     edges=0, early=[], late=[], q273=None,
                     active_oe_conflicts=0, active_oe_conflict_bits=0,
                     selected_cycles=[])

        def observe(pc, y, cycle):
            if state['previous_pc'] == 0x12A and pc == 0x127:
                if not selected(state['previous_pc']) or selected(pc):
                    raise ValueError('PROM clock polarity changed')
                if cycle != state['previous_cycle'] + 1:
                    raise ValueError('12A and 127 are not adjacent cycles')
                index = state['edges']
                if index % SAMPLE_DIVISOR == 0 and len(state['early']) < SAMPLE_COUNT:
                    previous = state['previous_y']
                    state['early'].append(previous)
                    state['late'].append(y)
                    state['selected_cycles'].append(cycle)
                    if state['q273'] is not None:
                        conflict = (state['q273'] ^ previous) & 0xF0
                        state['active_oe_conflicts'] += bool(conflict)
                        state['active_oe_conflict_bits'] += bin(conflict).count('1')
                    # OE high (three-state) during transparent 373 and the
                    # clock. It may stay high for Tx, or 373 LE must close
                    # on the sample before OE can safely go low.
                    state['q273'] = previous
                state['edges'] += 1
            state['previous_pc'] = pc
            state['previous_y'] = y
            state['previous_cycle'] = cycle

        result = instrument(observe)(
            mapping, scenario_for(base, controller_case, 256),
            cycles, mode='integrated', trace_limit=0)
        early = state['early']
        late = state['late']
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['trace_digest'] != saved['trace_digests']['256'] or
                result['trace_digest'] != old_parallel['trace_digest'] or
                state['edges'] != 312053 or len(early) != SAMPLE_COUNT or
                len(late) != SAMPLE_COUNT):
            raise ValueError(('whole-stream clock schedule changed', selector,
                              result['clean'], result['completed_cycles'], cycles,
                              result['trace_digest'] == saved['trace_digests']['256'],
                              result['trace_digest'] == old_parallel['trace_digest'],
                              state['edges'], len(early), len(late)))
        early_sha = hashlib.sha256(bytes(early)).hexdigest()
        late_sha = hashlib.sha256(bytes(late)).hexdigest()
        if (early_sha != saved['phases'][0]['banks']['256']['raw_y_sha256'] or
                late_sha != saved['phases'][1]['banks']['256']['raw_y_sha256'] or
                state['active_oe_conflicts'] !=
                old_parallel['active_parallel_q_conflict_before_clock_samples'] or
                state['active_oe_conflict_bits'] !=
                old_parallel['active_parallel_q_conflict_before_clock_bits']):
            raise ValueError(('sample or OE result differs from prior replay', selector))
        intervals = [later - earlier for earlier, later in zip(
            state['selected_cycles'], state['selected_cycles'][1:])]
        if set(intervals) != {1500}:
            raise ValueError(('qualified clock spacing changed', selector, set(intervals)))
        cases.append(dict(selector=selector,
                          trace_digest=result['trace_digest'],
                          whole_store_decode_hits=['12A'],
                          raw_12a_to_127_clock_edges=state['edges'],
                          qualified_clock_edges=len(early),
                          qualified_clock_period_prom_cycles=1500,
                          first_qualified_clock_cycles=state['selected_cycles'][:16],
                          early_sample_sha256=early_sha,
                          late_control_sample_sha256=late_sha,
                          enabled_373_preclock_conflicting_samples=state['active_oe_conflicts'],
                          enabled_373_preclock_conflicting_bits=state['active_oe_conflict_bits'],
                          assumed_373_disabled_preclock_conflicting_samples=0,
                          early_bus_data_errors=[row['filtered_data_errors'] for row
                              in saved['phases'][0]['banks']['256']['bus_scores']],
                          late_bus_data_errors=[row['filtered_data_errors'] for row
                              in saved['phases'][1]['banks']['256']['bus_scores']]))
        print('parallel clock', selector, 'raw edges', state['edges'],
              'qualified', len(early), 'unmasked conflicts',
              state['active_oe_conflicts'], flush=True)
    paths = (Path(__file__), EXECUTE, GATE, PRIOR, PARALLEL, TXREADY,
             MAPPINGS['q3'], *rom_paths)
    report = dict(experiment='whole-store PROM decode and parallel latch/OE event schedule',
                  model=dict(clock_decode=LITERALS,
                             clock_edge='inverted select rises at 12A-to-127; clocks before new 127 Y settles',
                             counter_divisor=SAMPLE_DIVISOR,
                             output_enable='assumed 373 OE high during transparent input and 273 clock; may go low only after 373 LE closes on the same byte before 127 Y changes, or remain high for Tx',
                             input='assumed Y bus to both D banks; photo suggests four shared D and Q pairs',
                             required_timing='12A Y valid >=20 ns before clock; 127 Y change >=5 ns after clock'),
                  cases=cases,
                  limitations=[
                      'The PROM literal gate and counter are executed as a model; their board nets and package realization are untraced.',
                      'The OE interval is explicitly assumed and removes logical contention; no actual enable waveform or analog current is measured.',
                      'The 20 ns setup and 5 ns hold minima are requirements, not measured propagation margins.',
                      'The DAC08 pin bus, analog line output and full controller-to-D127 connection remain conditional.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
