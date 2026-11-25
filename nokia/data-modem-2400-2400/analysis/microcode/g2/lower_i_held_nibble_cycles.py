"""Classify held-D3F8 bytes and exact periodic ROM/ALU motion in 3ED–3FA."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

INPUT_PC = 0x3F8
ROM_PC = 0x3F7
SCREEN_CYCLES = 512
PERIOD_CYCLES = 1580
ALU_PCS = (0x3F8, 0x3F9, 0x3FA)


def scenario_for(base, byte):
    scenario = copy.deepcopy(base)
    scenario['name'] += f'; held D3F8={byte:02X}, candidate PROM data-bit controls'
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = [byte]
    return scenario


def settled_period(sequence):
    """Earliest suffix that repeats >=4 times at its shortest period <=32."""
    for start in range(min(65, len(sequence))):
        for period in range(1, 33):
            if len(sequence) - start < 4 * period:
                continue
            if all(sequence[i] == sequence[i - period]
                   for i in range(start + period, len(sequence))):
                return dict(start_visit=start, period=period,
                            one_cycle=sequence[start:start + period])
    return None


def traced_run(mapping, scenario):
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, PERIOD_CYCLES,
                         mode='integrated', out=temporary,
                         trace_limit=PERIOD_CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != PERIOD_CYCLES:
        raise ValueError('held-byte trace incomplete')
    return result, trace


def run(out=HERE / 'results/lower-i-held-nibble-cycles.json'):
    _, unmodified = fixture()
    base = split_scenario(unmodified)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')
    classes = []
    for low in range(16):
        runs = []
        for high in range(16):
            byte = high * 16 + low
            summary = execute(mapping, scenario_for(base, byte), SCREEN_CYCLES,
                              mode='integrated', trace_limit=0)
            if not summary['clean']:
                raise ValueError(f'held byte {byte:02X} stopped')
            runs.append(dict(byte=byte, rom_visits=summary['address_counts'].get(ROM_PC, 0),
                             final_pc=summary['final_state']['pc'],
                             trace_digest=summary['trace_digest']))
        digests = {row['trace_digest'] for row in runs}
        if len(digests) != 1 or len({row['rom_visits'] for row in runs}) != 1:
            raise ValueError(f'high nibble changes low-nibble class {low:X}')
        classes.append(dict(low_nibble=low, high_bytes=[row['byte'] for row in runs],
                            rom_visits_512=runs[0]['rom_visits'],
                            final_pc_512=runs[0]['final_pc'],
                            unique_trace_digests=len(digests),
                            common_trace_digest=runs[0]['trace_digest']))
    periodic = []
    for entry in classes:
        if entry['rom_visits_512'] < 50:
            continue
        low = entry['low_nibble']
        result, trace = traced_run(mapping, scenario_for(base, low))
        rom_rows = [row for row in trace if row['pc'] == ROM_PC and
                    row['external_read'].get('selected_by_alu')]
        if len(rom_rows) < 150:
            raise ValueError(f'low nibble {low:X} did not sustain ROM reads')
        addresses = [row['external_read']['address'] for row in rom_rows]
        values = [row['external_read']['value'] for row in rom_rows]
        address_period = settled_period(addresses)
        value_period = settled_period(values)
        alu = {f'{pc:03X}': settled_period([
            row['alu']['y'] for row in trace if row['pc'] == pc])
            for pc in ALU_PCS}
        if (address_period is None or value_period is None or
                any(period is None for period in alu.values()) or
                address_period['period'] != value_period['period'] or
                any(period['period'] != address_period['period']
                    for period in alu.values())):
            raise ValueError(f'low nibble {low:X} lacks a shared settled period')
        periodic.append(dict(low_nibble=low, rom_visits=len(rom_rows),
                             rom_addresses=address_period, rom_bytes=value_period,
                             alu_y=alu, trace_digest=result['trace_digest']))
    periods = sorted({row['rom_addresses']['period'] for row in periodic})
    paths = [Path(__file__), HERE / 'lower_i_prom_data_route.py',
             HERE / 'lower_i_input_pipeline.py',
             HERE / 'independent_slice_addresses.py',
             HERE / 'independent_slice_fields.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             ASSUMED / 'execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='held D3F8 low-nibble periodic loop under candidate PROM-data controls',
                  fixture=dict(mapping=mapping['name'], q=5,
                               input_site='3F8', rom_site='3F7',
                               high_nibble_values=16, low_nibble_values=16,
                               screening_cycles=SCREEN_CYCLES,
                               periodic_trace_cycles=PERIOD_CYCLES,
                               minimum_repeats=4, maximum_period=32),
                  totals=dict(screened_bytes=256, nibble_classes=len(classes),
                              sustained_classes=len(periodic),
                              exited_classes=16 - len(periodic),
                              settled_periods=periods),
                  classes=classes, periodic=periodic,
                  limitations=[
                      'The paired PROM-data routes, inverters, latch captures and D3F8 input source are untraced hypotheses.',
                      'Held bytes reveal recurrence but do not replay the full controller bitstream; tested changing streams exit early.',
                      'ALU Y and ROM bytes are internal values, not traced DAC08 samples or recovered receive bits.',
                      'The microcycle divisor, DAC clock and byte wiring are unmeasured, so no physical carrier frequency is assigned.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
