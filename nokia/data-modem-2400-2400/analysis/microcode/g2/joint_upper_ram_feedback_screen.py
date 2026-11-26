"""Execute a labelled external 93422 counter/latch feedback candidate."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

EXECUTE = HERE.parent / 'assumed/execute.py'
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114811760.jpg'
VISITS = 768
CYCLES = 8 * VISITS + 47


def instrumented_execute():
    """Keep the shared emulator untouched and make each injection site explicit."""
    source = EXECUTE.read_text()
    patches = (
        ("    source_read=scenario['io']['read'];table=source_read['table'];rom_hash=None",
         "    source_read=scenario['io']['read'];table=source_read['table'];rom_hash=None\n"
         "    external_ram=[1]*256; external_address=0; external_latch=1\n"
         "    external_writes=0; external_reads=0; external_first_changed_read=None\n"
         "    external_loop_visits=0\n"
         "    external_ticks=(set(scenario['external_ram_address_tick_visits']) "
         "if 'external_ram_address_tick_visits' in scenario else None)\n"
         "    external_y={0x3F8:[],0x3F9:[],0x3FA:[]}"),
        ("            carry=carry_input.resolve(r)",
         "            if pc==scenario.get('external_ram_read_pc',0x3EB) and scenario.get('external_ram_feedback'):\n"
         "                lane=scenario.get('external_ram_lane','high')\n"
         "                external_read_address=(external_address+scenario.get('external_ram_read_offset',0))&255\n"
         "                d=((external_ram[external_read_address]&0xF0) if lane=='high' "
         "else (external_ram[external_read_address]&0x0E))|1\n"
         "                external_reads+=1\n"
         "                if d!=1 and external_first_changed_read is None:\n"
         "                    external_first_changed_read=dict(cycle=cycle,address=external_read_address,value=d)\n"
         "                read_event=dict(value=d,source='assumed_93422_ram',address=external_read_address,"
         "selected_by_alu=selects_d,status='hypothesis')\n"
         "            carry=carry_input.resolve(r)"),
        ("            carry_input.observe(result)",
         "            if (pc==0x3EC and scenario.get('external_ram_write') and\n"
         "                    (scenario.get('external_ram_write_until') is None or\n"
         "                     external_writes < scenario['external_ram_write_until'])):\n"
         "                external_ram[external_address]=external_latch\n"
         "                external_writes+=1\n"
         "            if pc==scenario.get('external_ram_latch_pc',0x3FA):\n"
         "                lane=scenario.get('external_ram_lane','high')\n"
         "                external_latch=((result['y']&0xF0) if lane=='high' "
         "else (result['y']&0x0E))|1\n"
         "            if pc in external_y:\n"
         "                external_y[pc].append(result['y'])\n"
         "            if pc==0x3EA:\n"
         "                if external_ticks is None or external_loop_visits in external_ticks:\n"
         "                    external_address=(external_address+1)&255\n"
         "                external_loop_visits+=1\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['external_ram_candidate']=dict(address=external_address,latch=external_latch,"
         "writes=external_writes,reads=external_reads,bytes=external_ram,"
         "first_changed_read=external_first_changed_read,loop_visits=external_loop_visits,"
         "y_by_pc=external_y)\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection site changed', old))
        source = source.replace(old, new)
    scope = {'__name__': 'joint_upper_ram_feedback_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def run(out=HERE / 'results/joint-upper-ram-feedback-screen.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    generator = random.Random(0x3557)
    stimulus = [generator.randrange(80, 177) for _ in range(256)]
    offered = stimulus + [127] * (VISITS - len(stimulus))
    cases = []
    for name, feedback, write, lane, latch_pc in (
            ('no_feedback', False, False, 'high', 0x3FA),
            ('read_only', True, False, 'high', 0x3FA),
            ('write_only', False, True, 'high', 0x3FA),
            ('feedback_high_3FA', True, True, 'high', 0x3FA),
            ('feedback_low_3FA', True, True, 'low', 0x3FA),
            ('feedback_high_3F9', True, True, 'high', 0x3F9)):
        scenario = scenario_for_full_byte(base, offered, 'complementary')
        scenario['external_ram_feedback'] = feedback
        scenario['external_ram_write'] = write
        scenario['external_ram_lane'] = lane
        scenario['external_ram_latch_pc'] = latch_pc
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         trace_limit=0)
        ram = result.pop('external_ram_candidate')
        cases.append(dict(name=name, clean=result['clean'],
                          completed_cycles=result['completed_cycles'],
                          d3f8_visits=result['address_counts'].get(0x3F8, 0),
                          final_pc=f"{result['final_state']['pc']:03X}",
                          loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                          trace_digest=result['trace_digest'],
                          final_q=result['final_state']['q'],
                          final_internal_ram=result['final_state']['ram'],
                          external_writes=ram['writes'],
                          external_reads=ram['reads'],
                          first_changed_read=ram['first_changed_read'],
                          external_noninitial=sum(value != 1 for value in ram['bytes']),
                          external_sha256=hashlib.sha256(bytes(ram['bytes'])).hexdigest(),
                          external_address=ram['address']))
        print(name, cases[-1]['d3f8_visits'], cases[-1]['final_pc'],
              cases[-1]['external_noninitial'], flush=True)
    by_name = {row['name']: row for row in cases}
    baseline = by_name['no_feedback']['trace_digest']
    if any(by_name[name]['d3f8_visits'] != VISITS or
           by_name[name]['trace_digest'] != baseline
           for name in ('read_only', 'write_only', 'feedback_low_3FA')):
        raise ValueError('baseline or low-nibble control changed')
    if any(by_name[name]['loop_exits'] != 1 or
           by_name[name]['d3f8_visits'] >= VISITS
           for name in ('feedback_high_3FA', 'feedback_high_3F9')):
        raise ValueError('high-nibble feedback exit changed')
    if by_name['write_only']['external_noninitial'] != 256:
        raise ValueError('candidate RAM writes did not cover all addresses')
    paths = (Path(__file__), EXECUTE, PHOTO,
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='candidate 93422 counter/latch feedback in executed mask-08 loop',
                  fixture=dict(visits=VISITS, cycles=CYCLES,
                               stimulus='256 deterministic ADC codes 80..176, then 512 held 127',
                               external_ram='256x8, initialized to 01',
                               address='modulo-256 counter increments at 3EA',
                               data='3FA or 3F9 Y nibble latched with D0 forced high',
                               write='latch written at 3EC, candidate inverted U18 D2/D4 pulse',
                               feedback='3EB D high or low nibble from RAM, D0 forced high'),
                  cases=cases,
                  limitations=['Counter cascade, RAM address/data pins, latch, write gate and readback are untraced.',
                               'Forced D0, chosen nibble and 3FA/3F9 latch site are assumptions to preserve the observed receive-loop mode.',
                               'This is a counterfactual wiring screen, not a verified echo canceller.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
