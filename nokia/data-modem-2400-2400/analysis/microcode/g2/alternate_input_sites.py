"""Inventory recurring D sites and test alternative ADC ingress hypotheses."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from adc_sample_path import DIBITS
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import receive, transmit

Q_SWEEP = HERE / 'results/photo-mapping-q-sweep.json'
ADC_CASES = (('q1', 2, 0x3EB), ('q1', 4, 0x3A7), ('q1', 255, 0x3C1),
             ('q2', 0, 0x12A), ('q3', 2, 0x3EB), ('q3', 4, 0x3A7),
             ('q4', 8, 0x12A), ('fitted_swapped', 1, 0x187))


def trace_run(mapping, scenario, cycles, directory):
    result = execute(mapping, scenario, cycles, mode='integrated',
                     out=directory, trace_limit=cycles)
    trace = [json.loads(line) for line in
             (directory / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != cycles:
        raise ValueError('incomplete real-PROM execution')
    return result, trace


def post_site_signatures(trace, initial_ram, initial_q, site, offered):
    """Retained RAM/Q before next site, grouped by the previous input byte."""
    ram = initial_ram[:]
    q = initial_q
    previous = None
    visits = 0
    signatures = defaultdict(set)
    for row in trace:
        if row['pc'] == site:
            if previous is not None and visits <= offered:
                signatures[previous].add((tuple(ram), q))
            previous = row['external_read']['value']
            visits += 1
        for index, value in row['registers'].items():
            ram[int(index)] = value
        q = row['q']
    return signatures, visits


def run(out):
    sweep = json.loads(Q_SWEEP.read_text())
    _, base = fixture()
    inventory = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for case in sweep['cases']:
            name = case['mapping']
            mapping = mapped(MAPPINGS[name])
            representative = {}
            for row in case['rows']:
                representative.setdefault(row['final_pc'], row['q'])
            for q in sorted(set(representative.values()) | {0, 5}):
                scenario = copy.deepcopy(base)
                scenario['initial']['q'] = q
                result, trace = trace_run(mapping, scenario, 2048, directory)
                counts = Counter(f"{row['pc']:03X}" for row in trace[256:]
                                 if row.get('external_read', {}).get('selected_by_alu')
                                 and row['external_read'].get('source') == 'scenario_pc_sequence')
                inventory.append(dict(mapping=name, initial_q=q,
                                      final_pc=f"{result['final_state']['pc']:03X}",
                                      recurring_d_sites={pc: count for pc, count in sorted(counts.items())
                                                         if count > 2},
                                      selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                      trace_digest=result['trace_digest']))
    site_set = sorted({pc for row in inventory for pc in row['recurring_d_sites']})
    if len(inventory) != 48 or site_set != ['127', '12A', '187', '38E', '3A7', '3C1', '3EB']:
        raise ValueError('recurrent D-site inventory changed')

    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference line stimulus did not recover its dibits')
    codes = [127 - sample for sample in pcm]
    adc_cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for name, q, site in ADC_CASES:
            mapping = mapped(MAPPINGS[name])
            order_maps = []
            for order, values in (('forward', codes), ('reverse', codes[::-1])):
                scenario = copy.deepcopy(base)
                scenario['initial']['q'] = q
                scenario['io']['read']['pc_sequences'][str(site)] = values
                result, trace = trace_run(mapping, scenario, 4096, directory)
                signatures, visits = post_site_signatures(
                    trace, scenario['initial']['ram'], q, site, len(values))
                order_maps.append(signatures)
                first = next(row['cycle'] for row in trace if row['pc'] == site)
                rom_after = [row['external_read']['address'] for row in trace
                             if row['cycle'] > first and
                             row.get('external_read', {}).get('selected_by_alu') and
                             'address' in row['external_read']]
                bus_addresses = defaultdict(set)
                for row in trace:
                    event = row.get('external_read', {})
                    if row['cycle'] > first and 'address' in event and not event['selected_by_alu']:
                        bus_addresses[f'{row["pc"]:03X}'].add(event['address'])
                adc_cases.append(dict(mapping=name, initial_q=q, site=f'{site:03X}',
                                      order=order, consumed=min(visits, len(values)),
                                      site_visits=visits,
                                      distinct_input_codes=len(signatures),
                                      max_states_per_code=max(map(len, signatures.values())),
                                      distinct_post_site_states=len({state for states in signatures.values()
                                                                     for state in states}),
                                      rom_reads_after_first_site=len(rom_after),
                                      rom_addresses=sorted(set(rom_after)),
                                      unconsumed_rom_bus_sites={pc: len(addresses)
                                                                for pc, addresses in sorted(bus_addresses.items())},
                                      final_pc=f"{result['final_state']['pc']:03X}",
                                      trace_digest=result['trace_digest']))
            adc_cases[-1]['same_byte_map_as_forward'] = order_maps[0] == order_maps[1]
    if any(row['max_states_per_code'] != 1 for row in adc_cases
           if row['site'] != '187') or any(row['same_byte_map_as_forward'] is False
                                     for row in adc_cases if row['order'] == 'reverse'
                                     and row['site'] != '187'):
        raise ValueError('memoryless alternate site changed')
    q3_a7 = [row for row in adc_cases if row['mapping'] == 'q3' and row['site'] == '3A7']
    if (len(q3_a7) != 2 or any(row['unconsumed_rom_bus_sites'].get('3B5') != 72
                                or row['rom_reads_after_first_site'] != 0 for row in q3_a7)):
        raise ValueError('q3 D3A7 ROM bus-versus-operand distinction changed')

    q1_mapping = mapped(MAPPINGS['q1'])
    q1_trigger = []
    for value in range(256):
        scenario = copy.deepcopy(base)
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences']['295'] = [value]
        result = execute(q1_mapping, scenario, 2048, mode='integrated', trace_limit=0)
        if not result['clean']:
            raise ValueError('q1 D127 byte sweep stopped')
        q1_trigger.append(dict(value=value, visits_127=result['address_counts'].get(0x127, 0),
                               visits_12c=result['address_counts'].get(0x12C, 0),
                               final_pc=f"{result['final_state']['pc']:03X}"))
    if ([(row['value'], row['visits_127'], row['visits_12c']) for row in q1_trigger
         if row['visits_12c'] > 100] != [(0, 1, 500)] or
            any(row['visits_127'] != 502 for row in q1_trigger[1:])):
        raise ValueError('q1 D127 zero trigger changed')

    fitted_controls = []
    fitted = mapped(MAPPINGS['fitted_swapped'])
    for value in (0, 1):
        scenario = copy.deepcopy(base)
        scenario['initial']['q'] = 1
        scenario['io']['read']['pc_sequences']['391'] = [value]
        result = execute(fitted, scenario, 512, mode='integrated', trace_limit=0)
        fitted_controls.append(dict(value=value, visits_187=result['address_counts'].get(0x187, 0),
                                    final_pc=f"{result['final_state']['pc']:03X}"))
    if fitted_controls != [dict(value=0, visits_187=8, final_pc='084'),
                           dict(value=1, visits_187=223, final_pc='187')]:
        raise ValueError('fitted D187 zero/nonzero control changed')

    sources = [Path(__file__), Q_SWEEP, HERE/'adc_sample_path.py',
               HERE/'reference_modem.py', HERE/'photo_controller_path.py',
               HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
               ASSUMED/'execute.py', *MAPPINGS.values()]
    report = dict(status='candidate alternate D-site screen, not recovered board inputs',
                  inventory=dict(runs=len(inventory), cycles_per_run=2048,
                                 recurrent_sites=site_set, cases=inventory),
                  adc=dict(coding='127 - signed reference PCM', samples=len(codes),
                           cycles_per_run=4096, cases=adc_cases),
                  q1_d127=dict(initial_q=0, tested_bytes=256,
                               zero_enters_12c_rom_loop=True,
                               nonzero_stays_at_127=True),
                  fitted_d187=dict(initial_q=1, controls=fitted_controls,
                                   note='187 is a PLP/BLT shift loop; order effects under one-new-sample-per-visit are not receiver proof.'),
                  limitations=['Representative Q values cover observed final-PC classes, not every Q/initial-RAM combination.',
                               'D bytes, ROM gate, and all photo-derived routes are scenario hypotheses.',
                               'An Am27S31 address may be driven on the bus even when the instruction ignores its data; only selected_by_alu reads count as ROM operands.',
                               'Post-site signatures include RAM and Q only; external state and analog sample timing are not modeled.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/alternate-input-sites.json')
    print(report['inventory']['recurrent_sites'], report['q1_d127'],
          report['fitted_d187']['controls'])
