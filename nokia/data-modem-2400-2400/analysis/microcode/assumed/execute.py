"""Bounded-memory execution of real PROMs under explicit mapping/scenario assumptions."""
import argparse
import hashlib
import json
import random
from contextlib import ExitStack
from collections import Counter
from pathlib import Path
from common import HERE, decode, digest, load, read, save, unconditional_transfer, table_targets, validate_brt_gate
from model import Am2901, SplitAm2901, X8X02, UnknownStack
from external_line import validate_external_line, external_line_value


class CarryInput:
    """Explicit constant or mapped/previous-carry input, shared with experiments."""
    def __init__(self,policy):
        self.policy=policy
        self.previous=policy['initial'] if isinstance(policy,dict) else policy
        self.counts=Counter()

    def resolve(self,row):
        if not isinstance(self.policy,dict):return self.policy
        if row[self.policy['select_field']]:
            value=self.previous;self.counts['feedback']+=1
            if value is None:
                value=self.policy['unknown'];self.counts['unknown_feedback']+=1
        else:
            value=row[self.policy['constant_field']];self.counts['mapped_constant']+=1
        self.counts[f'value_{value}']+=1
        return value

    def observe(self,result):
        self.previous=result['carry']


def validate_scenario(s):
    if s['status'] not in ('hypothesis','stub','recovered-from-data') or not s.get('evidence'):
        raise ValueError('scenario requires provenance')
    if s.get('stack_fallback') is not None:
        raise ValueError('stack repair is unsupported: diagnose mapping instead')
    clocked = s['inputs'].get('clocked_prom_bit')
    if clocked is not None:
        if (not isinstance(clocked, dict) or
                clocked.get('status') not in ('hypothesis', 'stub', 'recovered-from-data') or
                not clocked.get('evidence') or
                clocked.get('clock_chip') not in ('10', '11', '17', '18') or
                clocked.get('data_chip') not in ('10', '11', '17', '18') or
                type(clocked.get('clock_bit')) is not int or not 0 <= clocked['clock_bit'] < 8 or
                type(clocked.get('data_bit')) is not int or not 0 <= clocked['data_bit'] < 8 or
                type(clocked.get('edge_to')) is not int or clocked['edge_to'] not in (0, 1) or
                type(clocked.get('invert_data')) is not bool or
                type(clocked.get('initial')) is not int or clocked['initial'] not in (0, 1) or
                clocked.get('targets') != ['i0', 'a1']):
            raise ValueError('clocked PROM bit requires a sourced edge, data bit, initial level and I0/A1 targets')
        if ('0' in s['inputs'].get('instruction_bit_overrides', {}) or
                '1' in s['inputs'].get('register_address_bit_overrides', {}).get('a', {}) or
                any('0' in bits for bits in s['inputs'].get('instruction_bit_overrides_by_pc', {}).values()) or
                any('1' in fields.get('a', {}) for fields in
                    s['inputs'].get('register_address_bit_overrides_by_pc', {}).values())):
            raise ValueError('clocked PROM bit conflicts with I0/A1 overrides')
    overrides = s['inputs'].get('instruction_bit_overrides', {})
    if (not isinstance(overrides, dict) or any(
            not isinstance(bit, str) or not bit.isdecimal() or str(int(bit)) != bit
            or not 0 <= int(bit) < 9 or not isinstance(policy, dict)
            or type(policy.get('value')) is not int or policy['value'] not in (0, 1)
            or policy.get('status') not in ('hypothesis', 'stub', 'recovered-from-data')
            or not policy.get('evidence')
            for bit, policy in overrides.items())):
        raise ValueError('instruction bit overrides require indexed, provenance-owned constant bits')
    instruction_overrides_by_pc = s['inputs'].get('instruction_bit_overrides_by_pc', {})
    if (not isinstance(instruction_overrides_by_pc, dict) or any(
            not isinstance(pc, str) or not pc.isdecimal() or str(int(pc)) != pc
            or not 0 <= int(pc) < 1024 or not isinstance(bits, dict) or any(
                not isinstance(bit, str) or not bit.isdecimal() or str(int(bit)) != bit
                or not 0 <= int(bit) <= 8 or not isinstance(policy, dict)
                or type(policy.get('value')) is not int or policy['value'] not in (0, 1)
                or policy.get('status') not in ('hypothesis', 'stub', 'recovered-from-data')
                or not policy.get('evidence')
                for bit, policy in bits.items())
            for pc, bits in instruction_overrides_by_pc.items())):
        raise ValueError('PC instruction overrides require indexed, provenance-owned constant bits')
    address_overrides = s['inputs'].get('register_address_bit_overrides', {})
    if (not isinstance(address_overrides, dict) or any(
            field not in ('a', 'b', 'a_high', 'b_high') or
            (field.endswith('_high') and s['inputs'].get('slice_instruction') is None) or
            not isinstance(bits, dict) or any(
                not isinstance(bit, str) or not bit.isdecimal() or str(int(bit)) != bit
                or not 0 <= int(bit) < 4 or not isinstance(policy, dict)
                or type(policy.get('value')) is not int or policy['value'] not in (0, 1)
                or policy.get('status') not in ('hypothesis', 'stub', 'recovered-from-data')
                or not policy.get('evidence')
                for bit, policy in bits.items())
            for field, bits in address_overrides.items())):
        raise ValueError('register address overrides require indexed, provenance-owned constant bits')
    address_overrides_by_pc = s['inputs'].get('register_address_bit_overrides_by_pc', {})
    if (not isinstance(address_overrides_by_pc, dict) or any(
            not isinstance(pc, str) or not pc.isdecimal() or str(int(pc)) != pc
            or not 0 <= int(pc) < 1024 or not isinstance(fields, dict) or any(
                field not in ('a', 'b', 'a_high', 'b_high') or
                (field.endswith('_high') and s['inputs'].get('slice_instruction') is None) or
                not isinstance(bits, dict) or any(
                    not isinstance(bit, str) or not bit.isdecimal() or
                    str(int(bit)) != bit or not 0 <= int(bit) < 4 or
                    not isinstance(policy, dict) or
                    type(policy.get('value')) is not int or policy['value'] not in (0, 1) or
                    policy.get('status') not in ('hypothesis', 'stub', 'recovered-from-data') or
                    not policy.get('evidence')
                    for bit, policy in bits.items())
                for field, bits in fields.items())
            for pc, fields in address_overrides_by_pc.items())):
        raise ValueError('PC register address overrides require indexed, provenance-owned constant bits')
    logic_flags=s['inputs'].get('logic_flags')
    if 'logic_flags' in s['inputs']:
        if (not isinstance(logic_flags,dict) or logic_flags.get('mode') not in ('unknown','am2901b-ripple')
                or logic_flags.get('status') not in ('hypothesis','recovered-from-data','stub') or not logic_flags.get('evidence')):
            raise ValueError('logic flags require a supported mode and provenance')
    slice_instruction = s['inputs'].get('slice_instruction')
    if slice_instruction is not None:
        links = slice_instruction.get('high_from_low') if isinstance(slice_instruction, dict) else None
        undriven = slice_instruction.get('undriven_shift') if isinstance(slice_instruction, dict) else None
        if (not isinstance(links, dict) or not links or
                slice_instruction.get('status') not in ('hypothesis', 'stub', 'recovered-from-data')
                or not slice_instruction.get('evidence') or
                any(not isinstance(high, str) or not high.isdecimal() or
                    str(int(high)) != high or not 3 <= int(high) <= 8 or
                    type(low) is not int or not 0 <= low <= 8
                    for high, low in links.items())):
            raise ValueError('split-slice instruction links require provenance and valid bits')
        if (not isinstance(undriven, dict) or type(undriven.get('value')) is not int
                or undriven['value'] not in (0, 1)
                or undriven.get('status') not in ('hypothesis', 'stub', 'recovered-from-data')
                or not undriven.get('evidence')):
            raise ValueError('split-slice undriven shift level requires explicit provenance')
        if logic_flags is None or logic_flags['mode'] != 'am2901b-ripple':
            raise ValueError('split-slice model requires the explicit ripple flag model')
    c=s['condition'];d=s['dispatch']
    if 'brt_unconditional_gate' in c:
        validate_brt_gate(c['brt_unconditional_gate'])
    if c['mode'] not in ('constant','per-select','random','flags'):
        raise ValueError('unknown condition mode')
    if c['flag_timing'] not in ('current','previous'):
        raise ValueError('invalid flag timing')
    for key in ('per_select','polarity'):
        if len(c[key])!=8 or any(v not in (0,1) for v in c[key]):
            raise ValueError(f'invalid {key}')
    if len(c['sources'])!=8 or any(v not in ('constant','zero','sign','carry','overflow','external','random') for v in c['sources']):
        raise ValueError('invalid condition sources')
    if c['value'] not in (0,1) or c['unknown'] not in (0,1):
        raise ValueError('invalid condition defaults')
    indirect=s['indirect_branch']
    if indirect['source'] not in ('microword','constant','y','q') or indirect['status'] not in ('stub','hypothesis','recovered-from-data') or not indirect.get('evidence') or not 0<=indirect['value']<1024:
        raise ValueError('invalid indirect branch policy')
    if d['mode'] not in ('constant','sequence','random') or d['source'] not in ('scenario','y','q','previous_y'):
        raise ValueError('invalid dispatch mode/source')
    if not d['sequence'] or any(not isinstance(v,int) or v<0 for v in d['sequence']):
        raise ValueError('invalid dispatch sequence')
    if not isinstance(c.get('unconditional_requires_direct', True), bool):
        raise ValueError('unconditional_requires_direct must be boolean')
    for pc,t in [*d['tables'].items(), *s.get('branch_tables',{}).items()]:
        if not 0<=int(pc)<1024:raise ValueError('invalid dispatch site')
        table_targets(t)
        if t.get('index_source',d['source']) not in ('scenario','y','q','previous_y'):
            raise ValueError('invalid table index source')
        if t['status'] not in ('hypothesis','stub','recovered-from-data') or not t.get('evidence'):
            raise ValueError('dispatch requires provenance')
    tables=[*d['tables'].values(),*s.get('branch_tables',{}).values()]
    if d['source']=='previous_y' or any(t.get('index_source')=='previous_y' for t in tables):
        if type(d.get('initial_y')) is not int or not 0<=d['initial_y']<=255:
            raise ValueError('previous Y requires an explicit initial_y byte')
    if s['io']['read']['mode'] not in ('immediate','constant','table','am27s31','pc_table','pc_sequence'):
        raise ValueError('unknown IO read mode')
    source_read=s['io']['read']
    if source_read['mode']=='pc_table':
        values=source_read.get('pc_values')
        if not isinstance(values,dict) or any(not isinstance(pc,str) or not pc.isdecimal() or str(int(pc))!=pc or not 0<=int(pc)<1024 or type(value) is not int or not 0<=value<=255 for pc,value in values.items()):
            raise ValueError('invalid PC-keyed read bytes')
        if source_read.get('status') not in ('hypothesis','stub','recovered-from-data') or not source_read.get('evidence'):
            raise ValueError('PC-keyed reads require provenance')
    if source_read['mode']=='pc_sequence':
        sequences=source_read.get('pc_sequences')
        if (not isinstance(sequences,dict) or source_read.get('sequence_end')!='hold-last'
                or any(not isinstance(pc,str) or not pc.isdecimal() or str(int(pc))!=pc or not 0<=int(pc)<1024
                       or not isinstance(values,list) or not values or any(type(v) is not int or not 0<=v<=255 for v in values)
                       for pc,values in sequences.items())):
            raise ValueError('invalid PC-keyed read sequences')
        if source_read.get('status') not in ('hypothesis','stub','recovered-from-data') or not source_read.get('evidence'):
            raise ValueError('PC-keyed sequences require provenance')
    read_policy=s['io']['read'].get('address')
    if read_policy is not None:
        if source_read['mode'] not in ('am27s31','pc_sequence') or read_policy.get('source')!='previous_y':
            raise ValueError('address feedback requires Am27S31 previous_y policy')
        if source_read['mode']=='pc_sequence':
            pcs=read_policy.get('pcs')
            if (not isinstance(pcs,list) or not pcs or any(type(pc) is not int or not 0<=pc<1024 for pc in pcs)
                    or len(set(pcs))!=len(pcs) or any(str(pc) in source_read['pc_sequences'] for pc in pcs)):
                raise ValueError('ROM read sites must be unique PCs without sequence overrides')
        elif 'pcs' in read_policy:
            raise ValueError('ROM read sites require pc_sequence mode')
        if read_policy.get('bank') not in (0,256) or type(read_policy.get('initial_y')) is not int or not 0<=read_policy['initial_y']<=255:
            raise ValueError('invalid ROM bank/initial address')
        bank_by_pc=read_policy.get('bank_by_pc',{})
        if (not isinstance(bank_by_pc,dict) or
                any(not isinstance(pc,str) or not pc.isdecimal() or str(int(pc))!=pc
                    or not 0<=int(pc)<1024 or type(bank) is not int or bank not in (0,256)
                    or source_read['mode']!='pc_sequence' or int(pc) not in read_policy['pcs']
                    for pc,bank in bank_by_pc.items())):
            raise ValueError('ROM bank overrides must name selected PCs and banks 0 or 256')
        if read_policy.get('status') not in ('hypothesis','stub','recovered-from-data') or not read_policy.get('evidence'):
            raise ValueError('ROM address policy requires provenance')
        expected=s['io']['read'].get('expected_sha256','')
        if not isinstance(expected,str) or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('ROM feedback requires expected_sha256')
    if c['unconditional_select'] is not None and c['unconditional_select'] not in range(8):
        raise ValueError('invalid unconditional select')
    if any(not isinstance(v,int) or not 0<=v<=255 for v in s['io']['read']['table']) or not 0<=s['io']['read']['value']<=255:
        raise ValueError('read values must be bytes')
    if d['value']<0:
        raise ValueError('negative dispatch index')
    for w in s['io']['writes']:
        if not 0<=int(w['pc'])<1024 or w['status'] not in ('hypothesis','stub','recovered-from-data') or not w.get('evidence') or w.get('source','y') not in ('y','f','carry','zero','sign','overflow'):
            raise ValueError('invalid write rule')
    if not s['io']['read']['table']:
        raise ValueError('empty read table')
    initial=s['initial']
    if not 0<=initial['pc']<1024 or len(initial['ram'])!=16 or any(not 0<=v<=255 for v in initial['ram']) or not 0<=initial['q']<=255:
        raise ValueError('invalid initial state')
    carry=s['inputs']['carry']
    if isinstance(carry,dict):
        if carry['mode']!='mapped-or-previous' or carry['initial'] not in (0,1) or carry['unknown'] not in (0,1) or carry['status'] not in ('hypothesis','stub','recovered-from-data') or not carry.get('evidence'):
            raise ValueError('invalid carry policy')
    elif carry not in (0,1):raise ValueError('invalid carry input')
    validate_external_line(s['inputs']['external'])
    for key in ('ram_in','q_in'):
        if s['inputs'][key] not in (0,1): raise ValueError('invalid input bit')


def execute(mapping, scenario, cycles, seed=0, mode='sequencer', out=None, trace_limit=1000):
    with ExitStack() as stack:
        sinks={}
        if out:
            Path(out).mkdir(parents=True,exist_ok=True)
            sinks={name:stack.enter_context((Path(out)/name).open('w')) for name in ('trace.jsonl','io.jsonl')}
        return _execute(mapping,scenario,cycles,seed,mode,out,trace_limit,sinks)


def _execute(mapping, scenario, cycles, seed, mode, out, trace_limit, sinks):
    validate_scenario(scenario)
    if cycles<1 or trace_limit<0 or mode not in ('sequencer','integrated'):
        raise ValueError('invalid run limits/mode')
    lanes=load();rows=decode(mapping,lanes)
    if mode=='integrated' and any(k not in mapping['fields'] for k in ('i','a','b','d')):
        raise ValueError('integrated mode requires datapath fields')
    cond=scenario['condition'];dispatch=scenario['dispatch'];inputs=scenario['inputs']
    if inputs.get('logic_flags',{}).get('mode')=='am2901b-ripple' and mode!='integrated':
        raise ValueError('logical flag model requires integrated mode')
    slice_instruction = inputs.get('slice_instruction')
    clocked = inputs.get('clocked_prom_bit')
    if clocked is not None and mode != 'integrated':
        raise ValueError('clocked PROM bit requires integrated mode')
    if slice_instruction is not None and mode != 'integrated':
        raise ValueError('split-slice instruction model requires integrated mode')
    if any(k in mapping['fields'] for k in ('i_high', 'a_high', 'b_high')) and slice_instruction is None:
        raise ValueError('independent high-slice fields require split-slice model')
    if mode=='sequencer' and (cond['mode']=='flags' or dispatch['source']!='scenario' or scenario['indirect_branch']['source'] in ('y','q')):
        raise ValueError('datapath source requires integrated mode')
    all_tables=[*dispatch['tables'].values(),*scenario.get('branch_tables',{}).values()]
    if mode=='sequencer' and any(t.get('index_source','scenario')!='scenario' for t in all_tables):
        raise ValueError('table datapath source requires integrated mode')
    read_policy=scenario['io']['read'].get('address')
    if read_policy is not None and mode!='integrated':raise ValueError('ROM address feedback requires integrated mode')
    track_previous_y=dispatch['source']=='previous_y' or any(t.get('index_source')=='previous_y' for t in all_tables)
    for row in rows:
        if row['command']==4 and not row['direct'] and str(row['pc']) not in dispatch['tables']:
            raise ValueError(f"missing dispatch site {row['pc']:03x}")
    for site in scenario.get('branch_tables',{}):
        if rows[int(site)]['command'] != 6: raise ValueError('branch table site must be BRT')
    if isinstance(inputs['carry'],dict):
        if mode!='integrated':raise ValueError('carry feedback requires integrated mode')
        for key in ('select_field','constant_field'):
            field=inputs['carry'][key]
            if any(row.get(field) not in (0,1) for row in rows):raise ValueError('missing one-bit carry field')
    dispatch_targets={pc:table_targets(t) for pc,t in dispatch['tables'].items()}
    branch_targets={pc:table_targets(t) for pc,t in scenario.get('branch_tables',{}).items()}
    carry_input=CarryInput(inputs['carry'])
    rng=random.Random(seed); initial=scenario['initial']
    seq=X8X02(pc=initial['pc'])
    if slice_instruction is None:
        cpu=Am2901(ram=initial['ram'][:],q=initial['q'],
            logic_flags=inputs.get('logic_flags',{}).get('mode')=='am2901b-ripple')
    else:
        cpu=SplitAm2901(ram=initial['ram'][:],q=initial['q'],
            high_from_low={int(k):v for k,v in slice_instruction['high_from_low'].items()},
            undriven_shift=slice_instruction['undriven_shift']['value'])
    visited=Counter();edges=Counter();assumptions=Counter();events=[];depth=maximum=0
    stack_reads=stack_writes=underflows=overflows=unused=0
    source_read=scenario['io']['read'];table=source_read['table'];rom_hash=None
    if source_read['mode']=='am27s31' or read_policy is not None:
        p=HERE.parents[3]/'data-modem-2400-2400'/'am27s31dc-prom'/'nokia-modem-am27s31dc.bin'
        table=list(p.read_bytes());rom_hash=hashlib.sha256(bytes(table)).hexdigest()
        if not table: raise ValueError('empty Am27S31 dump')
        if read_policy is not None and (len(table)!=512 or rom_hash!=source_read['expected_sha256']):
            raise ValueError('Am27S31 feedback dump size/hash mismatch')
    read_counts=Counter();selected_reads=0;sequence_visits=Counter()
    instruction_overrides={int(bit): policy['value'] for bit, policy in
                           inputs.get('instruction_bit_overrides', {}).items()}
    instruction_overrides_by_pc={int(pc): {
        int(bit): policy['value'] for bit, policy in bits.items()}
        for pc, bits in inputs.get('instruction_bit_overrides_by_pc', {}).items()}
    address_overrides={field: {int(bit): policy['value'] for bit, policy in bits.items()}
                       for field, bits in inputs.get('register_address_bit_overrides', {}).items()}
    address_overrides_by_pc={int(pc): {
        field: {int(bit): policy['value'] for bit, policy in bits.items()}
        for field, bits in fields.items()}
        for pc, fields in inputs.get('register_address_bit_overrides_by_pc', {}).items()}
    writes={int(w['pc']):w for w in scenario['io']['writes']}
    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0
    routine_entries={r['branch'] for r in rows if r['command']==4 and r['direct']}
    routine_samples={}
    flags=dict(zero=None,sign=None,carry=None,overflow=None)
    h=hashlib.sha256(); stop='cycle limit'; completed=0
    clocked_q = clocked['initial'] if clocked is not None else None
    previous_clock = None
    clocked_captures = 0
    # Hash compact transitions incrementally, without storing a full history.
    for cycle in range(cycles):
        pc=seq.pc;r=rows[pc];c=r['command'];select=r['select'];visited[pc]+=1
        old_ram=tuple(cpu.ram) if mode=='integrated' else ();old_q=cpu.q
        if r['unused']: unused+=1
        previous=flags
        result=None;read_event=None
        if mode=='integrated':
            instruction=r['i']
            for bit, value in instruction_overrides.items():
                instruction=(instruction & ~(1 << bit)) | (value << bit)
                assumptions[f'instruction I{bit} scenario constant {value}']+=1
            for bit, value in instruction_overrides_by_pc.get(pc, {}).items():
                instruction=(instruction & ~(1 << bit)) | (value << bit)
                assumptions[f'instruction I{bit} PC {pc:03X} scenario {value}']+=1
            clocked_edge = False
            if clocked is not None:
                clock_level = (lanes[clocked['clock_chip']][pc] >> clocked['clock_bit']) & 1
                clocked_edge = (previous_clock is not None and
                                previous_clock == 1 - clocked['edge_to'] and
                                clock_level == clocked['edge_to'])
                if clocked_edge:
                    clocked_q = ((lanes[clocked['data_chip']][pc] >> clocked['data_bit']) & 1) ^ clocked['invert_data']
                    clocked_captures += 1
                previous_clock = clock_level
                instruction = (instruction & ~1) | clocked_q
                assumptions['clocked PROM I0/A1 hypothesis'] += 1
            high_instruction = (cpu.high_instruction(instruction, r.get('i_high'))
                                if slice_instruction is not None else instruction)
            selects_d = ((instruction & 7) in (5, 6, 7) or
                         (high_instruction & 7) in (5, 6, 7))
            register_address={'a': r['a'], 'b': r['b']}
            if slice_instruction is not None:
                register_address['a_high'] = r.get('a_high', r['a'])
                register_address['b_high'] = r.get('b_high', r['b'])
            for field, bits in address_overrides.items():
                for bit, value in bits.items():
                    register_address[field]=(register_address[field] & ~(1 << bit)) | (value << bit)
                    assumptions[f'register {field.upper()}{bit} scenario constant {value}']+=1
            for field, bits in address_overrides_by_pc.get(pc, {}).items():
                for bit, value in bits.items():
                    register_address[field]=(register_address[field] & ~(1 << bit)) | (value << bit)
                    assumptions[f'register {field.upper()}{bit} PC {pc:03X} scenario {value}']+=1
            if clocked is not None:
                register_address['a'] = (register_address['a'] & ~2) | (clocked_q << 1)
            d=r.get('d',source_read['value'])
            if 'd' not in r: assumptions['address-word D fallback']+=1
            if source_read['mode']=='pc_sequence' and read_policy is not None and pc in read_policy['pcs']:
                bank=read_policy.get('bank_by_pc',{}).get(str(pc),read_policy['bank'])
                address=bank+previous.get('y',read_policy['initial_y'])
                d=table[address];assumptions['table external read']+=1
                consumed=selects_d
                selected_reads+=consumed;read_counts[address]+=1
                read_event=dict(address=address,value=d,selected_by_alu=consumed,status=read_policy['status'])
            elif source_read['mode']=='constant': d=source_read['value'];assumptions['constant external read']+=1
            elif source_read['mode']=='pc_table':
                d=source_read['pc_values'].get(str(pc),source_read['value'])
                assumptions['PC-keyed external read']+=1
                read_event=dict(value=d,source='scenario_pc',selected_by_alu=selects_d,status=source_read['status'])
            elif source_read['mode']=='pc_sequence':
                sequence=source_read['pc_sequences'].get(str(pc))
                visit=index=None;held=False
                if sequence is None:
                    d=source_read['value']
                else:
                    visit=sequence_visits[pc];index=min(visit,len(sequence)-1);held=visit>=len(sequence)
                    d=sequence[index];sequence_visits[pc]+=1
                assumptions['PC-keyed external sequence read']+=1
                read_event=dict(value=d,source='scenario_pc_sequence',visit=visit,sequence_index=index,
                    held_last=held,selected_by_alu=selects_d,status=source_read['status'])
            elif source_read['mode'] in ('table','am27s31'):
                address=(read_policy['bank']+previous.get('y',read_policy['initial_y'])) if read_policy is not None else d%len(table)
                d=table[address]; assumptions['table external read']+=1
                if read_policy is not None:
                    consumed=selects_d
                    selected_reads+=consumed;read_counts[address]+=1
                    read_event=dict(address=address,value=d,selected_by_alu=consumed,status=read_policy['status'])
            carry=carry_input.resolve(r)
            if slice_instruction is None:
                result=cpu.step(instruction,register_address['a'],register_address['b'],d,carry,inputs['ram_in'],inputs['q_in'])
            else:
                result=cpu.step(instruction,register_address['a'],register_address['b'],d,carry,inputs['ram_in'],inputs['q_in'],
                                high_instruction=r.get('i_high'),
                                high_a=register_address['a_high'], high_b=register_address['b_high'])
            if slice_instruction is not None:
                assumptions['split-slice candidate instruction']+=1
            carry_input.observe(result)
            flags=result
            register_changes+=sum(a!=b for a,b in zip(old_ram,cpu.ram))+(old_q!=cpu.q)
        external_condition=None
        always=unconditional_transfer(r,scenario)
        if always:
            test=1;assumptions['unconditional direct transfer' if r['direct'] else 'unconditional computed transfer']+=1
        elif cond['mode']=='constant': test=cond['value']
        elif cond['mode']=='per-select': test=cond['per_select'][select]
        elif cond['mode']=='random': test=rng.getrandbits(1)
        else:
            source=cond['sources'][select]
            if source=='random': test=rng.getrandbits(1)
            elif source=='constant': test=cond['value']
            elif source=='external':
                test,external_condition=external_line_value(inputs['external'],cycle)
                assumptions['external condition']+=1
            else: test=(flags if cond['flag_timing']=='current' else previous)[source]
            if test is None:
                test=cond['unknown'];assumptions['unknown '+source]+=1
                if len(events)<32: events.append(dict(cycle=cycle,pc=pc,event='unknown '+source,value=test))
        # Unconditional transfers are invariant under per-select test polarity.
        if not always:
            test ^= cond['polarity'][select]
        branch=r['branch'];entry=None;index_source=None;trace_index=False
        branch_table=scenario.get('branch_tables',{}).get(str(pc)) if c==6 else None
        if c==6 and not r['direct'] and branch_table is None:
            policy=scenario['indirect_branch'];assumptions['indirect BRT '+policy['status']]+=1
            if policy['source']=='constant': branch=policy['value']
            elif policy['source']=='y': branch=result['y']
            elif policy['source']=='q': branch=cpu.q
        if test and ((c==4 and (not r['direct'] or str(pc) in dispatch_targets)) or branch_table is not None):
            t=branch_table if branch_table is not None else dispatch['tables'][str(pc)]
            targets=(branch_targets if branch_table is not None else dispatch_targets)[str(pc)];count=len(targets)
            index_source=t.get('index_source',dispatch['source'])
            trace_index='index_source' in t or index_source=='previous_y'
            if index_source=='y': index=result['y']
            elif index_source=='q': index=cpu.q
            elif index_source=='previous_y': index=previous.get('y',dispatch['initial_y'])
            elif dispatch['mode']=='constant': index=dispatch['value']
            elif dispatch['mode']=='sequence': index=dispatch['sequence'][dispatch_counts[pc]%len(dispatch['sequence'])]
            else: index=rng.randrange(count)
            entry=index%count;branch=targets[entry];dispatch_counts[pc]+=1
            assumptions['dispatch '+t['status']]+=1
        push=c==5 or (c==4 and test);pop=c in (2,3)
        before=dict(sp=seq.sp,depth=depth)
        if push:
            stack_writes+=1
            if depth>=4: overflows+=1
            depth+=1;maximum=max(maximum,depth)
        if pop:
            if c==3 or test: stack_reads+=1
            if depth<=0: underflows+=1
            depth-=1
        try: seq.step(c,branch,test)
        except UnknownStack as err:
            stop=str(err)
            if len(events)<32: events.append(dict(cycle=cycle,pc=pc,event=stop))
            break
        completed+=1;edges[(pc,seq.pc)]+=1
        if overflows or underflows:
            # Continue real circular-stack semantics; do not repair the model.
            if len(events)<32: events.append(dict(cycle=cycle,pc=pc,event='stack depth violation',depth=depth))
        h.update(bytes((pc&255,pc>>8,seq.pc&255,seq.pc>>8,test,cpu.q)))
        if slice_instruction is not None:
            h.update(bytes((high_instruction&255,high_instruction>>8)))
        if result: h.update(bytes(cpu.ram))
        if track_previous_y or read_policy is not None:h.update(bytes((result['y'],)))
        if isinstance(inputs['carry'],dict):h.update(bytes((2 if carry_input.previous is None else carry_input.previous,)))
        if pc in writes:
            w=writes[pc];value=result[w.get('source','y')] if result else w.get('value',0)
            io_count+=1
            if io_count<=trace_limit and 'io.jsonl' in sinks:
                record=dict(cycle=cycle,pc=pc,address=w['address'],value=value,status=w['status'],evidence=w['evidence'])
                sinks['io.jsonl'].write(json.dumps(record,sort_keys=True)+'\n')
        if trace_count<trace_limit or (pc in routine_entries and pc not in routine_samples):
            record=dict(cycle=cycle,pc=pc,raw=r['raw'],command=c,test=test,branch=branch,dispatch_entry=entry,
                stack_before=before,stack_after=dict(sp=seq.sp,depth=depth,values=seq.stack[:]),next_pc=seq.pc,
                registers={str(i):v for i,v in enumerate(cpu.ram) if mode=='integrated' and old_ram[i]!=v},q=cpu.q,alu=result)
            if isinstance(inputs['carry'],dict):record['carry_in']=carry
            if mode=='integrated' and (instruction_overrides or slice_instruction is not None):
                record['instruction_i']=instruction
            if mode=='integrated' and clocked is not None:
                record['instruction_i']=instruction
                record['clocked_prom_bit']=dict(q=clocked_q, edge=clocked_edge)
            if mode=='integrated' and slice_instruction is not None:
                record['instruction_i_high']=high_instruction
            if mode=='integrated' and (address_overrides or clocked is not None):
                record['register_address_a']=register_address['a']
                record['register_address_b']=register_address['b']
            if mode=='integrated' and slice_instruction is not None and (
                    any(k in r for k in ('a_high', 'b_high')) or
                    any(k in address_overrides for k in ('a_high', 'b_high')) or
                    any(k in address_overrides_by_pc.get(pc, {}) for k in ('a_high', 'b_high'))):
                record['register_address_a_high']=register_address['a_high']
                record['register_address_b_high']=register_address['b_high']
            if read_event is not None:record['external_read']=read_event
            if external_condition is not None:record['external_condition']=external_condition
            if trace_index:record.update(dispatch_input=index,dispatch_source=index_source)
            if pc in routine_entries and pc not in routine_samples: routine_samples[pc]=record
            if trace_count<trace_limit:
                trace_count+=1
                if 'trace.jsonl' in sinks: sinks['trace.jsonl'].write(json.dumps(record,sort_keys=True)+'\n')
    used={r['pc'] for r in rows if not r['unused']};coverage=len(used&visited.keys())/len(used)
    summary=dict(mapping=mapping['name'],mapping_digest=digest(mapping),scenario=scenario['name'],scenario_digest=digest(scenario),
        rom_hashes={c:hashlib.sha256(data).hexdigest() for c,data in lanes.items()},am27s31_hash=rom_hash,mode=mode,seed=seed,
        requested_cycles=cycles,completed_cycles=completed,stop=stop,coverage=coverage,visited=sorted(visited),
        address_counts=dict(visited),uncovered=sorted(used-visited.keys()),edge_counts={f'{a:03x}->{b:03x}':n for (a,b),n in sorted(edges.items())},
        stack=dict(max_depth=maximum,final_depth=depth,reads=stack_reads,writes=stack_writes,underflows=underflows,overflows=overflows),
        unused_word_executions=unused,assumption_counts=dict(assumptions),events=events,dispatch_counts=dict(dispatch_counts),
        register_changes=register_changes,routine_samples=routine_samples,io_writes=io_count,trace_digest=h.hexdigest(),final_state=dict(pc=seq.pc,sp=seq.sp,stack=seq.stack,ram=cpu.ram,q=cpu.q),
        clean=completed==cycles and not(underflows or overflows),
        interpretation='Runs under declared assumptions; neither recovered wiring nor verified Nokia execution.')
    if track_previous_y or read_policy is not None:summary['final_state']['previous_y']=flags['y']
    if read_policy is not None:summary['rom_reads']=dict(address_counts=dict(read_counts),selected_by_alu=selected_reads,policy=read_policy)
    if isinstance(inputs['carry'],dict):
        summary['carry_model']=dict(previous=carry_input.previous,counts=dict(carry_input.counts))
    if 'logic_flags' in inputs:summary['logic_flag_model']=inputs['logic_flags']
    if clocked is not None:
        summary['clocked_prom_bit_model']=clocked
        summary['clocked_prom_bit_captures']=clocked_captures
        summary['clocked_prom_bit_final_q']=clocked_q
    if slice_instruction is not None:
        summary['slice_instruction_model']=slice_instruction
        summary['undriven_shift_reads']=cpu.undriven_shift_reads
    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)
    if out:
        out=Path(out);out.mkdir(parents=True,exist_ok=True);save(out/'summary.json',summary)
        save(out/'mapping.json',mapping);save(out/'scenario.json',scenario)

    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mapping',type=Path,required=True);p.add_argument('--scenario',type=Path,required=True)
    p.add_argument('--mode',choices=['sequencer','integrated'],default='sequencer')
    p.add_argument('--cycles',type=int,default=1000000);p.add_argument('--seed',type=int,default=0)
    p.add_argument('--trace-limit',type=int,default=1000);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();s=execute(read(a.mapping),read(a.scenario),a.cycles,a.seed,a.mode,a.out,a.trace_limit)
    print(json.dumps({k:s[k] for k in ('completed_cycles','coverage','stop','clean')}))

if __name__=='__main__': main()
