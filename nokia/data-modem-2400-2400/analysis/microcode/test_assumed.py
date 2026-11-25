"""Behavioral checks for the assumption-driven workflow."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'assumed'))
from common import HERE, decode, field_value, load, read, validate
from analyze import graph, must_targets, search_address, walk, rank_layouts
from execute import CarryInput, execute, validate_scenario
from register_study import recover_register, table_semantics


class AssumedTests(unittest.TestCase):
    def setUp(self):
        self.mapping=read(HERE/'sequencer.json')
        self.scenario=read(HERE/'baseline.json')

    def test_clocked_prom_bit_captures_on_executed_edges(self):
        fixture_root=Path(__file__).resolve().parent/'g2/results/swapped-sine-loop'
        mapping=read(fixture_root/'phase-20-mapping.json')
        scenario=read(fixture_root/'phase-20-scenario.json')
        scenario['inputs']['clocked_prom_bit']=dict(
            status='hypothesis',evidence='Unit-test edge and hold behavior',
            clock_chip='10',clock_bit=0,edge_to=1,
            data_chip='10',data_bit=5,invert_data=True,
            initial=0,targets=['i0','a1'])
        with tempfile.TemporaryDirectory() as temporary:
            summary=execute(mapping,scenario,100,mode='integrated',out=temporary,trace_limit=100)
            trace=[json.loads(line) for line in
                   (Path(temporary)/'trace.jsonl').read_text().splitlines()]
        raw=load()['10']
        previous=None
        q=0
        captures=0
        for row in trace:
            pc=row['pc']
            clock=raw[pc]&1
            edge=previous == 0 and clock == 1
            if edge:
                q=1-((raw[pc]>>5)&1)
                captures+=1
            self.assertEqual(row['clocked_prom_bit'],dict(q=q,edge=edge))
            self.assertEqual(row['instruction_i']&1,q)
            self.assertEqual((row['register_address_a']>>1)&1,q)
            previous=clock
        self.assertGreater(captures,0)
        self.assertEqual(summary['clocked_prom_bit_captures'],captures)
        invalid=copy.deepcopy(scenario)
        invalid['inputs']['instruction_bit_overrides']={'0':dict(
            value=1,status='hypothesis',evidence='conflicting driver')}
        with self.assertRaisesRegex(ValueError,'conflicts'):
            validate_scenario(invalid)

    def test_pc_bit_overrides_take_precedence_and_require_provenance(self):
        fixture_root=Path(__file__).resolve().parent/'g2/results/swapped-sine-loop'
        mapping=read(fixture_root/'phase-20-mapping.json')
        scenario=read(fixture_root/'phase-20-scenario.json')
        policy=lambda value:dict(value=value,status='hypothesis',
                                  evidence='Diagnostic per-word latch phase')
        scenario['inputs']['instruction_bit_overrides']={'0':policy(0)}
        scenario['inputs']['instruction_bit_overrides_by_pc']={'1':{'0':policy(1)}}
        scenario['inputs']['register_address_bit_overrides']={'a':{'0':policy(0)}}
        scenario['inputs']['register_address_bit_overrides_by_pc']={
            '1':{'a':{'0':policy(1)}}}
        validate_scenario(scenario)
        with tempfile.TemporaryDirectory() as temporary:
            execute(mapping,scenario,2,mode='integrated',out=temporary,trace_limit=2)
            rows=[json.loads(line) for line in
                  (Path(temporary)/'trace.jsonl').read_text().splitlines()]
        self.assertEqual([row['pc'] for row in rows],[0,1])
        self.assertEqual([row['instruction_i'] & 1 for row in rows],[0,1])
        self.assertEqual([row['register_address_a'] & 1 for row in rows],[0,1])
        invalid=copy.deepcopy(scenario)
        invalid['inputs']['instruction_bit_overrides_by_pc']['01']={
            '0':policy(1)}
        with self.assertRaisesRegex(ValueError,'PC instruction overrides'):
            validate_scenario(invalid)
        invalid=copy.deepcopy(scenario)
        invalid['inputs']['register_address_bit_overrides_by_pc']['1']['a']['0'].pop('evidence')
        with self.assertRaisesRegex(ValueError,'PC register address overrides'):
            validate_scenario(invalid)

    def test_paired_components_nonzero_first_high_byte(self):
        from paired_components_study import scenario_for, inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'paired-components-study.json')
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            for profile in ('q1','q3'):
                mapping=read(HERE/config['profiles'][profile])
                for v in (1,128,32769,65535):
                    for entry in range(4):
                        scenario=scenario_for(config,profile,255,v,entry)
                        result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                        self.assertTrue(result['clean'])
                        trace=load_trace(out);finding=inspect(trace,scenario,profile,255,v,entry)
                        if profile=='q3' and v==1 and entry==0:
                            self.assertEqual(finding['expected_pairs'],[510,2])
                            self.assertEqual(finding['outcome'],'terminal')
                            altered=copy.deepcopy(trace)
                            output=next(r for r in altered if r['pc']==0x393)
                            output['alu']['f']=output['alu']['y']=0
                            with self.assertRaises(AssertionError):
                                inspect(altered,scenario,profile,255,v,entry)

    def test_handler_reply_and_transform_invariant(self):
        from handler_reply_study import current_loop_invariant, prestate, verify_poll_bytes
        from handler_timing_study import scenario_for_case, classify
        from defined_condition_fit import load_trace
        config=read(HERE/'handler-reply-study.json')
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            for profile in ('q1','q3'):
                mapping=read(HERE/config['profiles'][profile]);rows=decode(mapping)
                current=scenario_for_case(config,profile,'current','blt',250)
                current_loop_invariant(rows,current)
                bad=copy.deepcopy(rows);bad[0x3f7]['b']=0
                with self.assertRaisesRegex(AssertionError,'writes R0'):
                    current_loop_invariant(bad,current)
                bad=copy.deepcopy(rows);bad[0x3f7]['i'] &= 63
                with self.assertRaisesRegex(AssertionError,'writes Q'):
                    current_loop_invariant(bad,current)
                scenario=scenario_for_case(config,profile,'previous','plp',250)
                execute(mapping,scenario,384,mode='integrated',out=out,trace_limit=384)
                original=load_trace(out);state=prestate(original,0x1ec)
                reply=verify_poll_bytes(rows,state)
                self.assertEqual(reply,8 if profile=='q1' else 2)
                scenario['io']['read']['pc_sequences'][str(0x1ec)]=[1]*7+[reply]
                result=execute(mapping,scenario,384,mode='integrated',out=out,trace_limit=384)
                self.assertTrue(result['clean'])
                trace=load_trace(out)
                self.assertEqual(trace[:state['cycle']],original[:state['cycle']])
                self.assertEqual(classify(trace,scenario)['first_terminal'],state['cycle']+46)
                self.assertEqual(result['final_state']['ram'][12],state['ram'][4])

    def test_handler_timing_recurrence_and_reply_phase(self):
        from handler_timing_study import scenario_for_case, classify
        from defined_condition_fit import load_trace
        config = read(HERE/'handler-timing-study.json')
        with tempfile.TemporaryDirectory() as temporary:
            for profile in ('q1','q3'):
                mapping = read(HERE/config['profiles'][profile])
                for timing,replies in (('previous','plp'),('current','blt'),('previous','blt'),('current','plp')):
                    for q in (0,2,255):
                        scenario = scenario_for_case(config,profile,timing,replies,q)
                        result = execute(mapping,scenario,512,mode='integrated',out=Path(temporary),trace_limit=512)
                        self.assertTrue(result['clean'])
                        trace = load_trace(Path(temporary))
                        got = classify(trace,scenario)
                        matched = (timing=='previous') == (replies=='plp')
                        self.assertEqual(got['dispatch'] is not None,matched)
                        if matched:
                            expected = 'terminal' if q==255 or q==0 and timing=='current' else 'repeat'
                            self.assertEqual(got['outcome'],expected)
                        else:
                            self.assertEqual(got['outcome'],'repeat')
                            self.assertEqual(got['repeat']['period'],2)
                        # An unconsumed input transition prevents a recurrence
                        # proof even when CPU/stack states repeat.
                        delayed = copy.deepcopy(scenario)
                        delayed['io']['read']['pc_sequences'][str(0x084)] = [1]*1024+[0]
                        if got['outcome']=='terminal':
                            with self.assertRaisesRegex(AssertionError,'repeated state'):
                                classify(trace,delayed)

    def test_selector_prefix_mapping_and_independent_inputs(self):
        from selector_prefix_study import scenario_for, run_prefix, verify
        config = read(HERE/'selector-prefix-study.json')
        base, tables = (read(HERE/config[k]) for k in ('scenario','tables'))
        expected = dict(q1=(2,2,4), q2=(0,1,1), q3=(2,3,4), q4=(0,1,1),
                        fitted_original=(0,2,0), fitted_swapped=(0,0,0))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for profile,path in config['profiles'].items():
                mapping = read(HERE/path)
                rows = decode(mapping)
                scenario = scenario_for(base,tables,config,'previous_y',1)
                got = run_prefix(rows,scenario)
                event = got['event']
                self.assertEqual((event['q'],event['current_y'],event['previous_y']),expected[profile])
                verify(mapping,scenario,got,root/profile)
            for profile in ('q1','q3'):
                mapping = read(HERE/config['profiles'][profile])
                rows = decode(mapping)
                scenario = scenario_for(base,tables,config,'q',1,[165,94])
                got = run_prefix(rows,scenario)
                event = got['event']
                self.assertEqual((event['q'],event['entry'],event['handler']),(3,3,0x300))
                self.assertEqual([(w['pc'],w['after']) for w in event['q_writes']],[(2,165),(0x76,3)])
                self.assertEqual(event['current_y'],3 if profile=='q1' else 4)
                verify(mapping,scenario,got,root/f'split-{profile}')

    def test_q3_early_clear_capture_diversion(self):
        import random
        from final_blocks import early_scenario,inspect_early
        from defined_condition_fit import load_trace
        config=read(HERE/'final-blocks.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x43)
        cases=[(a,b,255,0,255) for a in (0,1,255) for b in (0,1,2,255)]
        cases += [tuple(rng.randrange(256) for _ in range(5)) for _ in range(64)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                sc=early_scenario(config,*values);result=execute(mapping,sc,128,mode='integrated',out=out,trace_limit=128)
                want=inspect_early(load_trace(out),result,sc,*values)
                if number%8==0:
                    other=list(values);other[2]^=255;sc=early_scenario(config,*other)
                    result=execute(mapping,sc,128,mode='integrated',out=out,trace_limit=128)
                    self.assertEqual(inspect_early(load_trace(out),result,sc,*other),want)
                    for kind in ('carry','late'):
                        sc=early_scenario(config,*values)
                        if kind=='carry':sc['condition']['sources'][3]='carry'
                        else:sc['inputs']['external']['events']=[[27,1]]
                        result=execute(mapping,sc,32,mode='integrated',out=out,trace_limit=32)
                        self.assertTrue(result['clean']);self.assertEqual(next(r for r in load_trace(out) if r['pc']==0x42)['next_pc'],0x45)

    def test_q3_current_flag_complement_exit(self):
        import random
        from final_blocks import current_scenario,inspect_current,check_current_exit
        from defined_condition_fit import load_trace
        config=read(HERE/'final-blocks.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x1dc)
        self.assertEqual(check_current_exit(mapping),65536)
        cases=[(c,d,a,255) for c in (6,126,254) for d in (0,255,(((c+2)&255)>>1)^255) for a in (0,255)]
        cases += [(6+8*rng.randrange(32),*[rng.randrange(256) for _ in range(3)]) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                sc=current_scenario(config,*values);result=execute(mapping,sc,192,mode='integrated',out=out,trace_limit=192)
                want=inspect_current(load_trace(out),result,*values)
                if number%8==0:
                    sc['io']['read']['pc_sequences'].update({str(pc):[rng.randrange(256)] for pc in (0xcf,0xe2,0xe3)})
                    result=execute(mapping,sc,192,mode='integrated',out=out,trace_limit=192)
                    self.assertEqual(inspect_current(load_trace(out),result,*values),want)

    def test_q3_outer_input_load_and_preserving_return_leaves(self):
        import random
        from input_leaves import scenario_for,inspect,check_guard,LOAD_INDICES,PRESERVE_INDICES
        from defined_condition_fit import load_trace
        config=read(HERE/'input-leaves.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x221)
        self.assertEqual(check_guard(mapping),dict(guard_pairs=65536,fallthrough_pairs=32640))
        cases=[(4,d,u,p) for d in LOAD_INDICES+PRESERVE_INDICES for u,p in ((0,0),(255,255))]
        cases += [(4+8*rng.randrange(32),rng.choice(LOAD_INDICES+PRESERVE_INDICES),rng.randrange(256),rng.randrange(256)) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                sc=scenario_for(config,*values);result=execute(mapping,sc,160,mode='integrated',out=out,trace_limit=160)
                want=inspect(load_trace(out),result,*values)
                if number%9==0:
                    other=list(values);other[2]^=255
                    if not want['load']:other[3]^=255
                    sc=scenario_for(config,*other)
                    sc['io']['read']['pc_sequences'].update({str(pc):[rng.randrange(256)] for pc in (0x2b5,0x2b6)})
                    result=execute(mapping,sc,160,mode='integrated',out=out,trace_limit=160)
                    self.assertEqual(inspect(load_trace(out),result,*other),want)
                if number%11==0:
                    for source in ('q','y'):
                        sc=scenario_for(config,*values,source);result=execute(mapping,sc,160,mode='integrated',out=out,trace_limit=160)
                        got=inspect(load_trace(out),result,*values,source)
                        if source=='q':self.assertEqual(got,want)
                        else:self.assertTrue(got['load'])

    def test_q3_startup_wait_captures_and_handler_dispatch(self):
        import random
        from startup_contract import scenario_for,inspect,prediction,check_waits
        from defined_condition_fit import load_trace
        from handler_timing_study import classify
        config=read(HERE/'startup-contract.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x100)
        self.assertEqual(check_waits(mapping),131072)
        cases=[(code,0,0,r,s,255,0,255) for code in (0,1,254,255) for r,s in ((0,255),(255,0))]
        cases += [(rng.randrange(256),rng.randrange(6),rng.randrange(6),*[rng.randrange(256) for _ in range(5)]) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                sc=scenario_for(config,*values,fail1=rng.randrange(1,256),fail2=rng.randrange(1,256));cycles=prediction(*values)['cycles']
                result=execute(mapping,sc,cycles,mode='integrated',out=out,trace_limit=cycles)
                want=inspect(load_trace(out),result,*values)
                if number%10==0:
                    other=list(values);other[5]^=255;other[7]^=255
                    sc=scenario_for(config,*other);split=rng.randrange(256)
                    sc['io']['read']['pc_sequences'].update({'2':[split],str(0x76):[(values[0]-split)&255]})
                    result=execute(mapping,sc,cycles,mode='integrated',out=out,trace_limit=cycles)
                    got=inspect(load_trace(out),result,*other)
                    self.assertEqual((got['ram'],got['q'],got['handler'],got['cycles']),(want['ram'],want['q'],want['handler'],want['cycles']))
            for pc in (0x117,0x106):
                sc=scenario_for(config,255,0,0,128,0,1,255,1);sc['io']['read']['pc_sequences'][str(pc)]=[255]
                result=execute(mapping,sc,96,mode='integrated',out=out,trace_limit=96)
                trace=load_trace(out);finding=classify(trace,sc)
                self.assertTrue(result['clean']);self.assertEqual(finding['outcome'],'repeat');self.assertEqual(finding['repeat']['period'],2)
                self.assertIsNone(finding['dispatch']);self.assertFalse(any(row['pc']==pc+2 for row in trace))

    def test_q3_handler2_alternate_carry_and_all_return_leaves(self):
        import random
        from handler2_alternate import scenario_for,inspect,check_arithmetic
        from defined_condition_fit import load_trace
        config=read(HERE/'handler2-alternate.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x1e0)
        self.assertEqual(check_arithmetic(mapping),dict(preparation_pairs=8192,leaf_cases=32768))
        cases=[(c,e,256-c,1,i,2) for c in (2,122,130,250) for e in (255-c,256-c) for i in range(4)]
        cases += [(2+8*rng.randrange(32),*[rng.randrange(256) for _ in range(3)],rng.randrange(4),rng.randrange(5)) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                want=inspect(load_trace(out),result,*values)
                if number%8==0:
                    # Bypassed 197 and the zero-operand instruction 1E2 cannot change the result.
                    scenario['io']['read']['pc_sequences'].update({str(pc):[rng.randrange(256)] for pc in (0x197,0x1e2)})
                    result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                    self.assertEqual(inspect(load_trace(out),result,*values),want)
                if number%11==0:
                    other=list(values);other[4]=(other[4]+1)%4
                    scenario=scenario_for(config,*other)
                    result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                    got=inspect(load_trace(out),result,*other)
                    self.assertEqual((got['ram'],got['q'],got['first_terminal']),(want['ram'],want['q'],want['first_terminal']))

                if number%13==0:
                    for kind in ('zero','late'):
                        scenario=scenario_for(config,*values)
                        if kind=='zero':scenario['condition']['sources'][7]='zero'
                        else:scenario['inputs']['external']['events']=[[93,1]]
                        result=execute(mapping,scenario,100,mode='integrated',out=out,trace_limit=100)
                        self.assertTrue(result['clean'])
                        self.assertEqual(next(r for r in load_trace(out) if r['pc']==0x195)['next_pc'],0x196)

    def test_q3_handler1_parity_and_timed_continuations(self):
        import random
        from handler1_branches import scenario_for,inspect,check_parity
        from defined_condition_fit import load_trace
        config=read(HERE/'handler1-branches.json');base=read(HERE/config['handler_configuration'])
        mapping=read(HERE/base['mapping']);rng=random.Random(0x178)
        self.assertEqual(check_parity(mapping),65536)
        cases=[(1,0,255,d,w,route) for d in (0,255) for w in (0,255) for route in ('high','low','rise')]
        cases += [(1+8*rng.randrange(32),*[rng.randrange(256) for _ in range(4)],rng.choice(('high','low','rise'))) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,240,mode='integrated',out=out,trace_limit=240)
                want=inspect(load_trace(out),result,*values)
                if number%12==0:
                    other=(*values[:4],values[4]^255,values[5]);scenario=scenario_for(config,*other)
                    result=execute(mapping,scenario,240,mode='integrated',out=out,trace_limit=240)
                    got=inspect(load_trace(out),result,*other)
                    self.assertEqual((got['ram'],got['q'],got['first_terminal']),(want['ram'],want['q'],want['first_terminal']))
                if values[-1]=='rise' and number%5==0:
                    scenario=scenario_for(config,*values);scenario['inputs']['external']['events'][1][0]+=1
                    result=execute(mapping,scenario,240,mode='integrated',out=out,trace_limit=240)
                    inspect(load_trace(out),result,*values[:-1],'low')
                if values[-1]=='low' and number%7==0:
                    scenario=scenario_for(config,*values);scenario['inputs']['external']['events'][0][0]+=1
                    result=execute(mapping,scenario,240,mode='integrated',out=out,trace_limit=240)
                    inspect(load_trace(out),result,*values[:-1],'high')

    def test_q3_handler4_alternate_preparation_and_sum_routes(self):
        import random
        from handler4_alternatives import scenario_for,inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'handler4-alternatives.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x230)
        cases=[(c,i,alt,d,u,v) for c in (4,252) for i in (3,4,5,6) for alt in (False,True)
               for d,u,v in ((0,0,0),(255,1,0),(255,0,1))]
        cases += [(4+8*rng.randrange(32),rng.choice((3,4,5,6)),bool(rng.randrange(2)),*[rng.randrange(256) for _ in range(3)]) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                want=inspect(load_trace(out),result,*values)
                if number%12==0:
                    # These reads only affect exposed arithmetic, not retained state or the constant selectors.
                    scenario['io']['read']['pc_sequences'].update({str(pc):[rng.randrange(256)] for pc in (0x252,0xf0,0xf3)})
                    result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                    self.assertEqual(inspect(load_trace(out),result,*values),want)
                if values[2] and number%7==0:
                    # Falling one instruction too late leaves the original 2A0 route selected.
                    scenario=scenario_for(config,*values);scenario['inputs']['external']['events']=[[71,0]]
                    result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                    normal=(*values[:2],False,*values[3:])
                    inspect(load_trace(out),result,*normal)

    def test_q3_handler4_bank_replacement_and_capture_preservation(self):
        import random
        from handler4_bank import scenario_for,inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'handler4-bank.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x200)
        cases=[(4,i,p,255,255,255) for i in range(7,16) for p in (0,255)]
        cases += [(4+8*rng.randrange(32),rng.randrange(7,16),*[rng.randrange(256) for _ in range(4)]) for _ in range(96)]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for number,values in enumerate(cases):
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                want=inspect(load_trace(out),result,*values)
                if number%9==0:
                    # These retained writes are replaced by later reads in this path.
                    pcs=(0x209,0x20d,0x28f,0x292)
                    scenario['io']['read']['pc_sequences'].update({str(pc):[rng.randrange(256)] for pc in pcs})
                    result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                    self.assertEqual(inspect(load_trace(out),result,*values),want)

    def test_q3_handler6_early_complement_and_reload_boundary(self):
        import random
        from handler6_early import scenario_for,inspect,check_carry
        from defined_condition_fit import load_trace
        config=read(HERE/'handler6-early.json');base=read(HERE/config['handler_configuration']);h=read(HERE/base['handler_config'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0xe0)
        self.assertEqual(check_carry(mapping),65536)
        cases=[(6,0,0xc0,255,1,0,255,0,255),(254,255,0xc1,255,1,0,255,255,0)]
        for _ in range(64):
            cases.append((6+8*rng.randrange(32),rng.randrange(256),rng.choice((0xc0,0xc1)),*[rng.randrange(256) for _ in range(6)]))
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for case,values in enumerate(cases):
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                want=inspect(load_trace(out),result,*values[:7])
                if case<2:self.assertEqual(want['extra_terminal_step'],1)
                if case%6==0:
                    other=list(values);other[7]^=255;other[8]^=255
                    if values[3]!=255:other[5]^=255
                    scenario=scenario_for(config,*other)
                    result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                    self.assertEqual(inspect(load_trace(out),result,*other[:7]),want)

    def test_q3_handler6_late_masked_exit_and_terminal_skip(self):
        import random
        from handler6_late import scenario_for,inspect,check_exit
        from defined_condition_fit import load_trace
        config=read(HERE/'handler6-late.json');base=read(HERE/config['handler_configuration']);h=read(HERE/base['handler_config'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0xce)
        self.assertEqual(check_exit(mapping)['direct_pairs'],6561)
        cases=[(6,0,'capture',255,255,255),(254,255,'late',0,255,255)]
        for _ in range(64):
            cases.append((6+8*rng.randrange(32),rng.randrange(256),rng.choice(('capture','late')),*[rng.randrange(256) for _ in range(3)]))
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for values in cases:
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                want=inspect(load_trace(out),result,*values)
                if values in cases[:2]:self.assertEqual(want['extra_terminal_step'],1)

    def test_q3_handler3_alternate_drains_preserve_paired_component(self):
        import random
        from handler3_drains import scenario_for,inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'handler3-drains.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x1ef)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for case in range(48):
                code=3+8*rng.randrange(32);index=case%4;values=[rng.randrange(256) for _ in range(6)]
                scenario=scenario_for(config,code,index,*values)
                result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                want=inspect(load_trace(out),result,index,*values)
                for k in (0,2,3):values[k]^=255
                scenario=scenario_for(config,code,index,*values)
                other=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                changed=inspect(load_trace(out),other,index,*values)
                self.assertEqual(want,changed)

    def test_q3_early_entry32_nested_indices_and_retained_input(self):
        import random
        from early_entry32 import scenario_for,inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'early-entry32.json');early=read(HERE/config['early_configuration']);h=read(HERE/early['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x32)
        cases=[]
        for i in range(4):
            for j in range(3):
                cases.append((i,j,1,2,2,255,0,255))
                for _ in range(4):cases.append((i,j,*[rng.randrange(256) for _ in range(6)]))
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for values in cases:
                scenario=scenario_for(config,*values)
                result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                want=inspect(load_trace(out),result,scenario,*values)
                if values[2:5]==(1,2,2):self.assertTrue(want['terminal'])

    def test_q3_early_entry22_skip_preserves_actual_loop_frame(self):
        import random
        from early_entry22 import scenario_for,inspect,inspect_local,check_arithmetic
        from defined_condition_fit import load_trace
        config=read(HERE/'early-entry22.json');early=read(HERE/config['early_configuration']);h=read(HERE/early['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x22)
        arithmetic=check_arithmetic(mapping)
        self.assertEqual(arithmetic['pop_pairs']+arithmetic['skip_pairs'],65536)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for case in range(64):
                a,shift,x,y,capture=[rng.randrange(256) for _ in range(5)]
                scenario=scenario_for(config,a,shift,x,y,capture)
                result=execute(mapping,scenario,192,mode='integrated',out=out,trace_limit=192)
                inspect(load_trace(out),result,scenario,a,shift,x,y,capture)
                ram=[rng.randrange(256) for _ in range(16)];q=0 if case%4==0 else rng.randrange(256)
                inspect_local(mapping,config,ram,q,a,shift,x,y,out)

    def test_q3_early_entry13_call_fed_carry_wait(self):
        import random
        from early_entry13 import scenario_for,inspect,check_threshold
        from defined_condition_fit import load_trace
        config=read(HERE/'early-entry13.json');early=read(HERE/config['early_configuration']);h=read(HERE/early['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x13)
        self.assertEqual(check_threshold(mapping)['return_pairs'],32896)
        with tempfile.TemporaryDirectory() as temp:
            for case in range(54):
                values=[rng.randrange(256) for _ in range(8)]
                if case<6:values[0]=0
                if case%3==0:values[5]=0
                delay=None if case%3==1 else rng.randrange(8)
                scenario=scenario_for(config,*values,delay);out=Path(temp)
                result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                inspect(load_trace(out),result,scenario,*values,delay)
                if case%6==0:
                    values[3]^=255
                    scenario=scenario_for(config,*values,delay)
                    other=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                    inspect(load_trace(out),other,scenario,*values,delay)
                    self.assertEqual(result['final_state']['ram'],other['final_state']['ram'])
                    self.assertEqual(result['final_state']['q'],other['final_state']['q'])

    def test_q3_early_wait_predicates_and_completing_entry(self):
        import random
        from early_wait import scenario_for,inspect,loop_pass,check_loop
        from defined_condition_fit import load_trace
        config=read(HERE/'early-wait.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rows=decode(mapping);rng=random.Random(0x5d)
        self.assertEqual(check_loop(mapping)['returns'],dict(previous=256,current=256))
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for _ in range(48):
                entry=rng.randrange(8);a,b,capture,tail=[rng.randrange(256) for _ in range(4)]
                scenario=scenario_for(config,entry,a,b,capture,tail)
                result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                inspect(load_trace(out),result,scenario,entry,capture,tail)
            for case in range(36):
                q=rng.randrange(256);ram=[rng.randrange(256) for _ in range(16)]
                ram[3]=[q,(-q)&255,rng.randrange(256)][case%3];d=rng.randrange(256)
                for timing in ('previous','current'):
                    scenario=scenario_for(config,0,1,1,1,1);scenario['initial']=dict(pc=0x5d,ram=ram[:],q=q)
                    scenario['condition']['flag_timing']=timing;scenario['io']['read']['pc_sequences'][str(0x60)]=[d]
                    want=loop_pass(rows,ram,q,d,scenario['inputs']['carry'])
                    result=execute(mapping,scenario,7,mode='integrated',trace_limit=0)
                    self.assertEqual(result['final_state']['ram'],want['ram'])
                    self.assertEqual(result['final_state']['q'],q)
                    self.assertEqual(result['final_state']['pc'],0x64 if want[timing+'_returns'] else 0x5d)
                    self.assertEqual(result['stack']['max_depth'],1)
                    self.assertEqual(result['stack']['final_depth'],0)

    def test_q3_handler2_timed_routes_and_wrap_boundary(self):
        import random
        from handler2_routes import scenario_for,inspect,prediction
        from defined_condition_fit import load_trace
        config=read(HERE/'handler2-routes.json');body=read(HERE/config['body_configuration']);h=read(HERE/body['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x1c3)
        cases=[]
        for route in config['routes']:
            for a,b in ((0,0),(255,1),(1,1)):
                cases.append((route,2,a,b,128,1,255,128))
            for _ in range(8):
                a,b,p,u,v=[rng.randrange(256) for _ in range(5)]
                cases.append((route,2+8*rng.randrange(32),a,b,p,rng.randrange(8),u,v))
        with tempfile.TemporaryDirectory() as temp:
            for route,code,a,b,payload,delay,u,v in cases:
                scenario=scenario_for(config,code,a,b,payload,delay,u,v,route);out=Path(temp)
                result=execute(mapping,scenario,384,mode='integrated',out=out,trace_limit=384)
                inspect(load_trace(out),result,scenario,a,b,payload,delay,u,v,route)
        self.assertEqual(prediction(1,1,17,0,255,1,'detour')['first_poll']-
                         prediction(1,1,17,0,255,1,'fallthrough')['first_poll'],-15)

    def test_q3_handler2_comparison_carry_and_payload(self):
        import random
        from handler2_body import scenario_for,inspect,check_arithmetic
        from defined_condition_fit import load_trace
        config=read(HERE/'handler2-body.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x18b)
        self.assertEqual(check_arithmetic(mapping),65536)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for _ in range(48):
                code=2+8*rng.randrange(32);a,b,payload=[rng.randrange(256) for _ in range(3)];delay=rng.randrange(8)
                result=execute(mapping,scenario_for(config,code,a,b,payload,delay),320,mode='integrated',out=out,trace_limit=320)
                inspect(load_trace(out),result,a,b,payload,delay)

    def test_q3_handler0_discards_intermediate_inputs(self):
        import random
        from handler0_study import scenario_for,inspect,check_local
        from defined_condition_fit import load_trace
        config=read(HERE/'handler0-study.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(0x11a)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for _ in range(48):
                code=8*rng.randrange(32);values=[rng.randrange(256) for _ in range(4)]
                result=execute(mapping,scenario_for(config,code,*values),160,mode='integrated',out=out,trace_limit=160)
                inspect(load_trace(out),result,code,*values)
            counts=check_local(mapping,config,out)
            self.assertTrue(all(r['returns']==1 and r['repeats']==255 for r in counts.values()))

    def test_q3_handler5_continuations_preserve_entry_07b_state(self):
        import random
        from handler5_branches import scenario_for,prediction,inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'handler5-branches.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rng=random.Random(345)
        with tempfile.TemporaryDirectory() as temporary:
            for case in range(48):
                code=5+8*rng.randrange(32);entry=case%3
                u,v,mask=[rng.randrange(256) for _ in range(3)]
                scenario=scenario_for(config,code,entry,u,v,mask);out=Path(temporary)
                summary=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                want=inspect(load_trace(out),summary,code,entry,u,v,mask)
                other=scenario_for(config,code,entry,u,v,mask^255)
                alternative=execute(mapping,other,160,mode='integrated',trace_limit=0)
                self.assertEqual(alternative['final_state']['ram'],want['ram'])
                self.assertEqual(alternative['final_state']['q'],want['q'])
                self.assertEqual(want['ram'][3],3)
                self.assertEqual((want['ram'][12],want['ram'][15]),(0,0))

    def test_q3_handler7_overflow_and_captured_comparison(self):
        from handler7_study import scenario_for,prediction,inspect,check_gate
        from defined_condition_fit import load_trace
        config=read(HERE/'handler7-study.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3']);rows=decode(mapping)
        cases=[(7,7,248,0),(7,8,248,0),(7,8,248,7),(7,8,248,8),(255,255,0,255),(255,255,1,255)]
        with tempfile.TemporaryDirectory() as temporary:
            for values in cases:
                scenario=scenario_for(config,*values);out=Path(temporary)
                summary=execute(mapping,scenario,128,mode='integrated',out=out,trace_limit=128)
                want=inspect(load_trace(out),summary,*values)
                steps,gate=check_gate(rows,scenario['inputs']['carry'],*values)
                self.assertEqual(want,gate)
        self.assertEqual(prediction(7,7,248,0)['route'],'direct')
        self.assertEqual(prediction(7,8,248,7)['route'],'all-transforms')
        self.assertEqual(prediction(7,8,248,8)['route'],'final-transform')
        self.assertEqual(prediction(255,255,1,255)['q'],0)

    def test_controller_frame_bridge_requires_completion_and_latch(self):
        from frame_dac_bridge import latched_frame
        report=read(HERE/'results/frame-dac-bridge/report.json')
        complete=next(r for r in report['runs'] if r['completions']==4)
        result=complete['controller'];initial=248
        self.assertEqual(latched_frame(result,initial),complete['latch'])
        missing=copy.deepcopy(result)
        missing['events']=[e for e in missing['events'] if not (e['kind']=='tx_complete' and e['value']==4)]
        with self.assertRaisesRegex(ValueError,'preceded complete'):latched_frame(missing,initial)
        unlatched=copy.deepcopy(result)
        unlatched['events']=[e for e in unlatched['events'] if e['pc'] not in (0x8d7,0x8da)]
        self.assertIsNone(latched_frame(unlatched,initial))
        for r in report['runs']:
            if r['completions']<4:
                self.assertIsNone(latched_frame(r['controller'],initial));self.assertFalse(r['microcode_started'])

    def test_controller_frame_bridge_operand_and_recurring_dac(self):
        from frame_dac_bridge import scenario_for_frame,inspect_micro
        from rom_study import load_rom
        from defined_condition_fit import load_trace
        from dac0830 import replay
        config=read(HERE/'frame-dac-bridge.json');sine=read(HERE/config['sine_config'])
        mapping=read(HERE/sine['profiles']['q3']);rom=load_rom(sine)
        with tempfile.TemporaryDirectory() as temporary:
            for case in config['frames']:
                wire=case['expected_wire'];scenario=scenario_for_frame(config,wire)
                summary=execute(mapping,scenario,256,mode='integrated',out=Path(temporary),trace_limit=256)
                self.assertTrue(summary['clean']);trace=load_trace(Path(temporary))
                finding=inspect_micro(trace,scenario,wire,rom)
                for pc,index in config['bindings'].items():
                    rows=[r for r in trace if r['pc']==int(pc)]
                    self.assertTrue(rows)
                    self.assertTrue(all(r['external_read']['value']==wire[index] for r in rows))
                dac=replay(trace,read(HERE/config['dac_config']),'first_low','per_load')
                self.assertEqual(dac['dac_register'],34 if wire[0]==133 else 146)
                self.assertEqual(finding['update_cycles'],list(range(55,256,12)))
                self.assertEqual(finding['quarter_sine'],wire[0]==5)

    def test_external_line_event_validation_and_boundaries(self):
        from external_line import validate_external_line,external_line_value
        policy=dict(mode='cycle-events',initial=1,events=[[3,0],[7,1]],status='stub',evidence='test clocked input')
        validate_external_line(policy)
        self.assertEqual([external_line_value(policy,n)[0] for n in (0,2,3,6,7,100)],[1,1,0,0,1,1])
        self.assertEqual(external_line_value(policy,3)[1]['event_index'],0)
        for events in ([[3,0],[3,1]],[[4,0],[2,1]],[[-1,0]],[[True,0]],[[2,7]],[[2]]):
            with self.assertRaises(ValueError):validate_external_line(dict(policy,events=events))
        with self.assertRaises(ValueError):validate_external_line(dict(policy,evidence=''))
        with self.assertRaises(ValueError):validate_external_line(dict(policy,initial=2))

    def test_external_line_delayed_loop_release_and_recurrence_guard(self):
        from defined_condition_fit import load_trace
        from handler_timing_study import classify
        p=HERE/'results/handler-timing-study/q3-previous-plp-03'
        mapping,scenario=read(p/'mapping.json'),read(p/'scenario.json')
        scenario['initial']=dict(pc=0x1f9,ram=[0]*16,q=0)
        scenario['condition']['sources'][0]='external'
        scenario['inputs']['external']=dict(mode='cycle-events',initial=0,events=[[10,1]],status='stub',evidence='release at cycle 10')
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            result=execute(mapping,scenario,12,mode='integrated',out=out,trace_limit=12)
            self.assertTrue(result['clean']);self.assertEqual(result['final_state']['pc'],0x1fa)
            self.assertEqual(result['stack']['final_depth'],0)
            trace=load_trace(out)
            self.assertEqual([row['cycle'] for row in trace if row['pc']==0x1ea],[2,4,6,8,10])
            self.assertEqual([row['test'] for row in trace if row['pc']==0x1ea],[1,1,1,1,0])
            with self.assertRaisesRegex(AssertionError,'bound did not establish'):
                classify(trace[:8],scenario)
            held=copy.deepcopy(scenario);held['inputs']['external']=0
            result=execute(mapping,held,12,mode='integrated',out=out/'held',trace_limit=12)
            self.assertEqual(result['final_state']['pc'],0x1ea)
            self.assertEqual(classify(load_trace(out/'held'),held)['repeat']['period'],2)

    def test_external_line_handler3_boot_and_branch_boundaries(self):
        from external_line_study import scenario_for,inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'external-line-study.json');h=read(HERE/config['handler_configuration'])
        mapping=read(HERE/h['profiles']['q3'])
        with tempfile.TemporaryDirectory() as temporary:
            for timing in ('previous','current'):
                for edge in (3,4,43,44):
                    scenario=scenario_for(config,timing,251,edge);out=Path(temporary)/f'{timing}-{edge}'
                    summary=execute(mapping,scenario,512,mode='integrated',out=out,trace_limit=512)
                    self.assertTrue(summary['clean']);inspect(load_trace(out),scenario,edge,timing)

    def test_q3_input_tail_three_routes_and_full_return(self):
        import random
        from input_tail_study import scenario_for,probe,prediction,check,verify_core
        config=read(HERE/'input-tail-study.json');p=HERE/config['base']
        mapping,base=read(p/'mapping.json'),read(p/'scenario.json');rows=decode(mapping)
        rng=random.Random(0x2ec);routes=set()
        with tempfile.TemporaryDirectory() as temporary:
            for case in range(96):
                ram=[rng.randrange(256) for _ in range(16)];q=rng.randrange(256)
                inputs={pc:rng.randrange(256) for pc in [*range(0x2ec,0x2fd),*range(0x2e0,0x2e5),0x21b,0x225]}
                s1=case%2;scenario=scenario_for(base,config,ram,q,inputs,s1)
                got=probe(rows,scenario,True);want=prediction(ram,q,inputs,s1);check(got,want)
                verify_core(mapping,scenario,got,Path(temporary)/'core');routes.add(want['route'])
                other=scenario_for(base,config,ram,q,inputs,1-s1)
                alternative=probe(rows,other)
                self.assertEqual((got['ram'],got['q']),(alternative['ram'],alternative['q']))
                self.assertEqual(got['q'],inputs[0x225])
                self.assertEqual(got['cycles'],{'comparison':28,'selector':32,'reload-mask':39}[want['route']])
        self.assertEqual(routes,{'comparison','selector','reload-mask'})

    def test_q3_paired_wait_high_byte_and_preceding_input(self):
        import random
        from pair_wait_study import scenario_for,probe,prediction,check,verify_core,fixture
        from defined_condition_fit import load_trace
        config=read(HERE/'pair-wait-study.json');p=HERE/config['base']
        mapping,base=read(p/'mapping.json'),read(p/'scenario.json');rows=decode(mapping)
        rng=random.Random(370);outcomes=set()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for case in range(64):
                ram=[rng.randrange(256) for _ in range(16)];q=rng.randrange(256);d=rng.randrange(256)
                source='scenario' if case%2 else 'previous_y';index=case%4 if source=='scenario' else d%4
                scenario=scenario_for(base,config,ram,q,index,d,source)
                got=probe(rows,scenario,True);check(got,prediction(ram,q,index,d))
                verify_core(mapping,scenario,got,root/'core');outcomes.add(got['outcome'])
                self.assertEqual(got['ram'][4:8],ram[4:8])
            ram,q=fixture(0x8001)
            want=prediction(ram,q,0,1)
            self.assertEqual(want['output'][2:],[2,0]);self.assertEqual(want['outcome'],'return')
            ram,q=fixture(0x1234)
            for source,index in [('previous_y',3),('y',0)]:
                scenario=scenario_for(base,config,ram,q,0,3,source)
                summary=execute(mapping,scenario,40,mode='integrated',out=root/source,trace_limit=40)
                self.assertTrue(summary['clean'])
                call=next(row for row in load_trace(root/source) if row['pc']==0x376)
                self.assertEqual(call['next_pc'],0x379+4*index)
        self.assertEqual(outcomes,{'return','repeat'})

    def test_q3_full_carry_helper_return_mask_and_recurrence(self):
        import random
        from carry_helper_study import scenario_for,probe,prediction,check,verify_core,inspect_reset
        from defined_condition_fit import load_trace
        config=read(HERE/'carry-helper-study.json');base_path=HERE/config['base']
        mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
        rng=random.Random(366);outcomes=set()
        with tempfile.TemporaryDirectory() as temporary:
            for case in range(96):
                ram=[rng.randrange(256) for _ in range(16)];q=rng.randrange(256)
                inputs={pc:rng.randrange(256) for pc in range(0x366,0x370)};s5=case%2
                scenario=scenario_for(base,config,ram,q,inputs,s5)
                got=probe(rows,scenario,record=True);want=prediction(ram,q,inputs,s5);check(got,want)
                verify_core(mapping,scenario,got,Path(temporary)/'core');outcomes.add(got['outcome'])
                self.assertEqual(got['ram'][0],ram[0] if got['outcome']=='repeat' else inputs[0x36f]&q)
                self.assertEqual(got['period'],3 if got['outcome']=='repeat' else None)
        self.assertEqual(outcomes,{'return','repeat'})
        p=HERE/config['reset'];calls=inspect_reset(load_trace(p),read(p/'scenario.json'))
        self.assertEqual((calls[0]['entry_cycle'],calls[0]['return_cycle']),(79,87))
        self.assertEqual(calls[0]['prediction']['ram'][:4],[1,255,255,0])

    def test_q3_conditional_helpers_arbitrary_inputs_and_returns(self):
        import random
        from branch_helpers_study import scenario_for,probe,prediction,check
        from reset_helpers_study import verify_core
        config=read(HERE/'branch-helpers-study.json');base_path=HERE/config['base']
        mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
        rng=random.Random(335357);paths={}
        with tempfile.TemporaryDirectory() as temporary:
            for entry in (0x270,0x335,0x357):
                helper=config['helpers'][str(entry)];paths[entry]=set()
                for case in range(64):
                    ram=[rng.randrange(256) for _ in range(16)];q=rng.randrange(256)
                    inputs={pc:rng.randrange(256) for pc in range(entry,helper['end']+1)}
                    s5,s6=case%2,(case//2)%2
                    scenario=scenario_for(base,config,entry,ram,q,inputs,s5,s6)
                    got=probe(rows,scenario,helper,record=True)
                    want=prediction(entry,ram,q,inputs,s5,s6);check(got,want)
                    paths[entry].add(tuple(want['pcs']))
                    verify_core(mapping,scenario,helper,got,Path(temporary)/'core')
        self.assertEqual({entry:len(p) for entry,p in paths.items()},{0x270:2,0x335:4,0x357:3})
        self.assertTrue(all(not ({0x273,0x279,0x27a}&set(p)) for p in paths[0x270]))

    def test_q3_short_helpers_preserve_transient_order(self):
        from short_helpers_study import prediction,fixture,inspect_reset
        from reset_helpers_study import scenario_for,probe,verify_core
        from defined_condition_fit import load_trace
        config=read(HERE/'short-helpers-study.json');base_path=HERE/config['base']
        mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for key,helper in config['helpers'].items():
                entry=int(key);ram,q,d=fixture(entry,1,127)
                if entry==0x04c:ram[0]=165;ram[3]=90
                scenario=scenario_for(base,config,entry,ram,q,d)
                got=probe(rows,scenario,helper,record=True);want=prediction(entry,ram,q,d)
                self.assertEqual((got['ram'],got['q']),(want['ram'],want['q']))
                self.assertEqual([t['alu']['y'] for t in got['trace'][1:]],want['y'])
                verify_core(mapping,scenario,helper,got,root/key)
            ram=list(range(16));ram[0]=1;ram[4]=7
            a=prediction(0x238,ram,99,1);b=prediction(0x240,ram,99,1)
            self.assertEqual((a['ram'],a['q']),(b['ram'],b['q']))
            self.assertEqual(a['y'],[0,0,2,1,1,0,7,1])
            self.assertEqual(b['y'],[0,1,1,0,2,0,7,1])
        calls=inspect_reset(load_trace(base_path),base,config)
        self.assertEqual(calls,[])

    def test_q3_reset_helpers_half_boundaries_and_negation(self):
        from reset_helpers_study import prediction,scenario_for,probe,verify_core,inspect_reset
        from defined_condition_fit import load_trace
        config=read(HERE/'reset-helpers-study.json');base_path=HERE/config['base']
        mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for r9,expected in ((0,255),(127,192),(128,64),(254,127),(255,0)):
                ram=[(37*i+19)&255 for i in range(16)];ram[9]=r9
                scenario=scenario_for(base,config,0x06f,ram,255,1)
                got=probe(rows,scenario,config['helpers']['111'],record=True)
                self.assertEqual((got['ram'][0],got['ram'][2],got['q']),(expected,ram[8],0))
                verify_core(mapping,scenario,config['helpers']['111'],got,root/f'half-{r9}')
            ram=list(range(16));ram[0]=255
            scenario=scenario_for(base,config,0x112,ram,255,2)
            got=probe(rows,scenario,config['helpers']['274'],record=True)
            self.assertEqual((got['ram'][2],got['ram'][4],got['q']),(1,1,255))
            verify_core(mapping,scenario,config['helpers']['274'],got,root/'negation')
        calls=inspect_reset(load_trace(base_path),base)
        self.assertEqual([c['entry'] for c in calls],[0x06f,0x112,0x112])

    def test_plan_execution_acceptance_keeps_failure_gates(self):
        from plan_validation import acceptance
        def run(mode,cycles):
            return dict(summary=dict(mode=mode,clean=True,completed_cycles=cycles,requested_cycles=cycles,
                        unused_word_executions=0,stack=dict(max_depth=4)),
                        replay_equal=True,saved_prefix_equal=True)
        runs=[run('sequencer',1000000),run('integrated',2000000)]
        sweep=dict(visited=list(range(941)),all_clean=True)
        self.assertTrue(acceptance(runs,sweep,.9)['execution_acceptance_met'])
        self.assertFalse(acceptance(runs,dict(sweep,visited=list(range(294))),.9)['execution_acceptance_met'])
        for mutate in ('clean','replay','stack','short','prefix'):
            broken=copy.deepcopy(runs)
            if mutate=='clean':broken[0]['summary']['clean']=False
            elif mutate=='replay':broken[0]['replay_equal']=False
            elif mutate=='stack':broken[0]['summary']['stack']['max_depth']=5
            elif mutate=='short':broken[1]['summary']['completed_cycles']=1999999
            else:broken[0]['saved_prefix_equal']=False
            self.assertFalse(acceptance(broken,sweep,.9)['execution_acceptance_met'])
        self.assertFalse(acceptance([],sweep,.9)['execution_acceptance_met'])

    def test_dac0830_level_buffers_and_unknown_startup(self):
        from dac0830 import DAC0830
        pins=dict(ile=1,cs_n=0,wr1_n=1,wr2_n=1,xfer_n=0)
        dac=DAC0830()
        self.assertIsNone(dac.drive(123,**pins)['dac_register'])
        pins['wr2_n']=0
        self.assertIsNone(dac.drive(123,**pins)['dac_register'])
        pins['wr2_n']=1;pins['wr1_n']=0
        self.assertEqual(dac.drive(17,**pins)['input_register'],17)
        self.assertEqual(dac.drive(34,**pins)['input_register'],34)
        self.assertIsNone(dac.dac_register)
        pins['wr1_n']=1
        self.assertEqual(dac.drive(99,**pins)['input_register'],34)
        pins['wr2_n']=0
        self.assertEqual(dac.drive(99,**pins)['dac_register'],34)
        pins['wr1_n']=0
        self.assertEqual(dac.drive(255,**pins)['dac_register'],255)
        pins['ile']=0
        self.assertEqual(dac.drive(0,**pins)['dac_register'],255)
        pins['ile']=1;pins['cs_n']=1
        self.assertEqual(dac.drive(0,**pins)['dac_register'],255)
        with self.assertRaises(ValueError):DAC0830(256,0)
        with self.assertRaises(ValueError):dac.drive(0,**dict(pins,wr1_n=2))

    def test_hypothetical_dac_sine_routes(self):
        from dac0830 import replay
        from sine_operand_study import scenario_for_phase
        from defined_condition_fit import load_trace
        config=read(HERE/'dac-output-study.json');sine=read(HERE/config['sine_config'])
        mapping=read(HERE/sine['profiles']['q3'])
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'run'
            for phase,low in ((53,254),(54,0),(64,8)):
                execute(mapping,scenario_for_phase(sine,'q3',phase),160,mode='integrated',out=out,trace_limit=160)
                trace=load_trace(out)
                self.assertEqual(replay(trace,config,'first_low','per_load')['dac_register'],low)
                self.assertIsNone(replay(trace,config,'first_low','load_only')['dac_register'])
                self.assertEqual(replay(trace,config,'all_four','terminal')['dac_register'],0)
                later=replay(trace,config,'first_low','terminal')
                self.assertEqual([e['cycle'] for e in later['events'] if e['action']=='transfer-open'],[110])
            bad=copy.deepcopy(config);bad['routes']['first_low']['source']='untraced_bus'
            with self.assertRaises(ValueError):replay(trace,bad,'first_low','per_load')
            bad=copy.deepcopy(config);bad['status']='recovered-from-data'
            with self.assertRaises(ValueError):replay(trace,bad,'first_low','per_load')

    def test_handler4_sum_carry_and_xor_skip(self):
        from handler4_study import scenario_for, capture, prediction, probe, verify_full
        from defined_condition_fit import load_trace
        config=read(HERE/'handler4-study.json')
        mapping=read(HERE/config['mapping']);rows=decode(mapping)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for captured in (0,255):
                scenario=scenario_for(config,0,0,captured)
                prefix_path=root/f'prefix-{captured}'
                snapshot=capture(mapping,scenario,prefix_path)
                prefix=load_trace(prefix_path)
                for a,b,r7 in config['witnesses']:
                    if r7!=captured:continue
                    got=probe(rows,scenario,snapshot,a,b);want=prediction(snapshot,a,b)
                    self.assertEqual((got['ram'],got['q'],got['cycles']),
                                     (want['ram'],want['q'],want['cycles']))
                    verify_full(mapping,scenario_for(config,a,b,captured),snapshot,got,want,
                                root/f'case-{captured}-{a}-{b}',prefix)
                self.assertEqual(probe(rows,scenario,snapshot,1,0)['q'],1+int(captured==255))
                self.assertEqual(probe(rows,scenario,snapshot,255,0)['q'],0)
                self.assertEqual(probe(rows,scenario,snapshot,255,1)['q'],255)

    def test_handler1_wrapped_sum_and_timing(self):
        from handler1_study import scenario_for, prediction, check_sum, inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'handler1-study.json')
        mapping=read(HERE/config['mapping']);rows=decode(mapping)
        for u,v,half in ((0,0,0),(255,1,0),(128,128,0),(255,255,127),(128,127,127)):
            self.assertEqual(check_sum(rows,u,v),half)
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'run'
            for code,u,v in config['witnesses']:
                scenario=scenario_for(config,code,u,v)
                result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                self.assertTrue(result['clean'])
                inspect(load_trace(out),scenario,code,u,v)
                self.assertEqual(result['final_state']['ram'],prediction(code,u,v)['ram'])
            trace=load_trace(out)
            next(t for t in trace if t['pc']==0x16a)['registers']['14']=99
            with self.assertRaises(AssertionError):inspect(trace,scenario,code,u,v)
        self.assertEqual(prediction(1,1,1)['first_terminal'],197)
        self.assertEqual(prediction(249,255,128)['first_terminal'],223)

    def test_handler6_masked_capture_and_drain(self):
        from handler6_study import scenario_for, prediction, inspect
        from defined_condition_fit import load_trace
        config=read(HERE/'handler6-study.json')
        mapping=read(HERE/config['mapping'])
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'run'
            for code,captured in config['witnesses']:
                scenario=scenario_for(config,code,captured)
                result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                self.assertTrue(result['clean'])
                trace=load_trace(out)
                inspect(trace,scenario,code,captured)
                self.assertEqual(result['final_state']['ram'],prediction(code,captured)['ram'])
            # The logical carry at the mask feeds the following increment.
            scenario=scenario_for(config,6,7)
            execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
            trace=load_trace(out)
            next(t for t in trace if t['pc']==0x0ad)['alu']['carry']=0
            with self.assertRaises(AssertionError):inspect(trace,scenario,6,7)
        self.assertEqual(prediction(254,255)['incremented'],0)
        self.assertEqual(prediction(254,254)['half'],127)
        self.assertEqual(prediction(126,255)['first_terminal'],131)

    def test_q3_direct_register_destinations(self):
        from q3_register_contract import scenario_for, prediction
        from register_contract_study import capture, resume, verify_full
        config = read(HERE/'q3-register-contract.json')
        base_path = HERE/config['base']
        mapping, base = read(base_path/'mapping.json'), read(base_path/'scenario.json')
        rows = decode(mapping)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = capture(mapping,base,config,root/'prefix')
            self.assertEqual((snapshot['cycle'],snapshot['depth']), (188,4))
            for number,(payload,first,second) in enumerate(config['witnesses']):
                scenario = scenario_for(base,config,payload,first,second)
                got = resume(rows,scenario,snapshot,payload,first,second,read_values=[first,second])
                want = prediction(snapshot,payload,base['io']['read']['value'],first,second)
                self.assertEqual(got['ram'],want['ram'])
                self.assertEqual([d['register'] for d in got['dispatches']],[first,second])
                self.assertEqual((got['cycles'],got['q']),(42,payload))
                verify_full(mapping,scenario,config,snapshot,got,root/f'case-{number}')
            # Using the q2 address adjustment under q3 must select a different register.
            scenario = scenario_for(base,config,1,6,7)
            wrong = resume(rows,scenario,snapshot,1,6,7)
            self.assertNotEqual(wrong['dispatches'][0]['register'],6)

    def test_register_contract_restores_real_reset_stack(self):
        from register_contract_study import capture, scenario_for, resume, verify_full
        from model import UnknownStack
        config = read(HERE/'register-contract-study.json')
        base_path = HERE/config['base']
        mapping = read(base_path/'mapping.json')
        base = read(base_path/'scenario.json')
        rows = decode(mapping)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = capture(mapping, base, config, root/'prefix')
            self.assertEqual((snapshot['pc'], snapshot['depth'], snapshot['cycle']), (0x225, 4, 186))
            for number,(payload,first,second,adjust,actual_second) in enumerate((
                    (1,6,7,True,7), (1,6,7,False,2), (2,5,0,True,0), (255,6,15,True,15))):
                scenario = scenario_for(base, config, payload, first, second, snapshot['ram'][6], adjust)
                got = resume(rows, scenario, snapshot, payload, first, second, adjust)
                self.assertEqual([d['register'] for d in got['dispatches']], [first,actual_second])
                self.assertEqual((got['cycles'], got['max_depth'], got['q']), (42,4,payload))
                if first == 5:
                    self.assertEqual(got['ram'][5], 100)
                if payload == 255:
                    self.assertEqual((got['ram'][6], got['ram'][15]), (127,127))
                verify_full(mapping,scenario,config,snapshot,got,root/f'case-{number}')
            broken = copy.deepcopy(snapshot)
            broken['stack'][broken['sp']] = None
            scenario = scenario_for(base,config,1,6,7,snapshot['ram'][6])
            with self.assertRaises(UnknownStack):
                resume(rows,scenario,broken,1,6,7)

    def test_indexed_tail_address_feedback_and_overwrite(self):
        from indexed_tail_study import probe, local_scenario, inspect_reset
        from nested_reset_study import scenario_for
        from defined_condition_fit import load_trace
        config = read(HERE/'indexed-tail-study.json')
        mapping = read(HERE/config['mapping'])
        rows = decode(mapping)
        base = read(HERE/config['scenario'])
        for source, q, d, indices in (
                ('previous_y', 0, 7, [198, 7]),
                ('previous_y', 2, 7, [198, 6]),
                ('y', 1, 0, [165, 0]),
                ('q', 255, 255, [255, 255])):
            ram = config['initial_ram'][:]
            ram[1], ram[6] = d^0xa5, (2*d+0x33)&255
            got = probe(rows, base, ram, q, d, source)
            self.assertEqual([t['index'] for t in got['trace'] if t['index'] is not None], indices)
            self.assertEqual([i for i,t in enumerate(got['trace']) if t['index'] is not None], [7,16])
            self.assertEqual((got['cycles'], got['max_depth'], got['q']), (20, 1, q))
            if source == 'previous_y':
                self.assertEqual(got['ram'][6], q>>1)
                if q == 0:
                    self.assertEqual(got['ram'][7], 0)
            if source == 'y':
                self.assertEqual(got['ram'][5], 127)  # First store of zero was overwritten.
            scenario = local_scenario(base, config, ram, q, d, source)
            result = execute(mapping, scenario, 20, mode='integrated', trace_limit=0)
            self.assertTrue(result['clean'])
            self.assertEqual(result['final_state']['ram'], got['ram'])
            self.assertEqual(result['final_state']['pc'], 0x084)
        reset_config = read(HERE/config['reset_config'])
        reset_base = read(HERE/reset_config['scenario'])
        tables = read(HERE/reset_config['tables'])
        with tempfile.TemporaryDirectory() as temporary:
            for source, entries in (('scenario',[10,15]), ('y',[0,0]), ('q',[12,12]), ('previous_y',[1,1])):
                scenario = scenario_for(reset_base, tables, reset_config, 204)
                for pc in (0x07e, 0x081):
                    scenario['dispatch']['tables'][str(pc)]['index_source'] = source
                result = execute(mapping, scenario, 256, seed=115, mode='integrated',
                                 out=Path(temporary), trace_limit=256)
                self.assertTrue(result['clean'])
                got = inspect_reset(load_trace(Path(temporary)), 204, source)
                self.assertEqual([t['entry'] for t in got['dispatches']], entries)
                self.assertEqual(got['prediction']['stored_value'], 102)
                self.assertEqual(got['final_ram'][15], 102 if source == 'scenario' else 205)

    def test_affine_helper_skip_and_reset_consumers(self):
        from affine_tail_study import probe, local_scenario, inspect_reset, selected_registers
        from defined_condition_fit import load_trace
        config = read(HERE/'affine-tail-study.json')
        self.assertEqual(selected_registers(dict(i=(2<<6)|2, a=15, b=0)), {15})
        base = read(HERE/config['scenario'])
        for path in config['profiles'].values():
            mapping = read(HERE/path)
            rows = decode(mapping)
            self.assertTrue(all(rows[p]['i'] & 7 not in (5, 6, 7) for p in range(0x28e, 0x296)))
            for r0, r1, q, skip, final0, final15 in (
                    (1, 0, 255, False, 255, 0), (1, 0, 255, True, 1, 2),
                    (7, 255, 0, False, 0, 255), (7, 255, 0, True, 7, 6)):
                ram = config['initial_ram'][:]
                ram[0], ram[1] = r0, r1
                got = probe(rows, base, ram, q, 93, skip)
                expected = ram[:]
                expected[0], expected[3], expected[15] = final0, r0, final15
                self.assertEqual(got['ram'], expected)
                self.assertEqual(got['q'], q)
                scenario = local_scenario(base, config, ram, q, 93, skip)
                run = execute(mapping, scenario, got['cycles'], mode='integrated', trace_limit=0)
                self.assertTrue(run['clean'])
                self.assertEqual(run['final_state']['pc'], 0x214)
                self.assertEqual(run['final_state']['ram'], expected)
        rows = decode(read(HERE/config['profiles']['q2']))
        trace = load_trace(HERE/'results/nested-reset-study/seed-0115')
        helper = inspect_reset(trace, rows)[0]
        self.assertEqual(helper['entry_q'], 204)
        self.assertEqual(helper['return_ram'][15], 205)
        self.assertEqual(helper['results']['0']['first_selected_read']['pc'], 0x216)
        self.assertIsNone(helper['results']['15']['first_selected_read'])
        self.assertEqual(helper['results']['15']['first_overwrite']['pc'], 0x099)
        self.assertEqual([t['next_pc'] for t in helper['tail_tests']], [0x078, 0x079, 0x07a])

    def test_nested_reset_reaches_actual_four_frame_call(self):
        from nested_reset_study import scenario_for, inspect
        from defined_condition_fit import load_trace
        config = read(HERE/'nested-reset-study.json')
        mapping = read(HERE/config['mapping'])
        rows = decode(mapping)
        base = read(HERE/config['scenario'])
        tables = read(HERE/config['tables'])
        with tempfile.TemporaryDirectory() as temporary:
            before = None
            for source in ('scenario', 'y', 'q', 'previous_y'):
                scenario = scenario_for(base, tables, config, 204)
                scenario['dispatch']['tables'][str(0x2c4)]['index_source'] = source
                result = execute(mapping, scenario, 256, seed=115, mode='integrated',
                                 out=Path(temporary), trace_limit=256)
                self.assertTrue(result['clean'])
                trace = load_trace(Path(temporary))
                call = inspect(trace, rows, scenario, 204)[0]
                self.assertEqual(call['entry_q'], 0)
                self.assertEqual(call['entry_q_writer']['pc'], 0x2f3)
                self.assertEqual(call['caller_depth'], 2)
                self.assertEqual(call['return_depth'], 2)
                self.assertEqual(result['stack']['max_depth'], 4)
                self.assertEqual(call['nested_target'], 0x225 if source == 'scenario' else 0x2b3)
                self.assertEqual(call['return_q'], 204 if source == 'scenario' else 0)
                prefix = trace[:call['nested_cycle']]
                if before is not None:
                    self.assertEqual(prefix, before)
                before = prefix

    def test_nested_prepare_preserves_or_replaces_q_by_leaf(self):
        from nested_prepare_study import fixture, prediction, probe, scenario_for
        from common import table_targets
        config = read(HERE/'nested-prepare-study.json')
        mapping = read(HERE/config['mapping'])
        rows = decode(mapping)
        base = read(HERE/config['scenario'])
        tables = read(HERE/config['tables'])['dispatch']['tables']
        for pc in (0x21f, 0x2c4):
            base['dispatch']['tables'][str(pc)] = tables[str(pc)]
        targets = table_targets(tables[str(0x2c4)])
        for source, q, d, target, final_q in (
                ('y', 255, 255, 0x2b3, 255),
                ('q', 1, 255, 0x22d, 1),
                ('q', 2, 255, 0x224, 255),
                ('q', 3, 255, 0x225, 255),
                ('previous_y', 1, 74, 0x22b, 1)):
            ram, reads = fixture(config, q, d)
            want = prediction(ram, q, d, reads, targets, source, config['outer_index'])
            self.assertEqual(want['target'], target)
            self.assertEqual(want['q'], final_q)
            got = probe(rows, base, ram, q, d, reads, source, config['outer_index'], targets)
            self.assertEqual((got['pc'], got['ram'], got['q'], got['max_depth']),
                             (0x220, want['ram'], final_q, 2))
            scenario = scenario_for(base, config, ram, q, d, reads, source)
            result = execute(mapping, scenario, got['cycles'], mode='integrated', trace_limit=0)
            self.assertTrue(result['clean'])
            self.assertEqual(result['final_state']['ram'], want['ram'])
            self.assertEqual(result['final_state']['q'], final_q)
            self.assertEqual(result['stack']['final_depth'], 0)

    def test_independent_capture_high_byte_exit(self):
        from paired_capture_study import scenario_for, inspect
        from defined_condition_fit import load_trace
        config = read(HERE/'paired-capture-study.json')
        mapping = read(HERE/config['mapping'])
        base = read(HERE/config['scenario'])
        with tempfile.TemporaryDirectory() as temporary:
            for low, high, entry, expected, releases in (
                    (1, 0, 0, 2, True), (128, 0, 0, 256, False),
                    (1, 128, 1, 2, True), (255, 255, 2, 0, True)):
                scenario = scenario_for(base, config, low, high, entry)
                result = execute(mapping, scenario, config['cycles'], mode='integrated',
                                 out=Path(temporary), trace_limit=config['cycles'])
                self.assertTrue(result['clean'])
                trace = load_trace(Path(temporary))
                observed = inspect(trace, low, high, entry)
                self.assertEqual(observed['expected_pair'], expected)
                self.assertEqual(observed['releases'], releases)
                # Detect a trace that silently replaces the real low-byte output.
                changed = copy.deepcopy(trace)
                output = next(t for t in changed if t['pc'] == 0x394+4*entry)
                output['alu']['f'] ^= 1
                with self.assertRaises(AssertionError):
                    inspect(changed, low, high, entry)

    def test_fixed_condition_graph_and_replay(self):
        from constant_condition_study import fixed_tests
        from context_branch_study import witness
        rows=decode(self.mapping)
        scenario=read(HERE/'results/constant-condition-study/gated-scenario.json')
        baseline=graph(rows,scenario)
        constrained=graph(rows,scenario,test_policy=fixed_tests)
        self.assertFalse(constrained['exceptions'])
        self.assertEqual(len(constrained['reached']),796)
        self.assertTrue(set(constrained['reached'])<set(baseline['reached']))
        for pc in (0x2d9,0x3bd):
            path=witness(rows,scenario,pc,test_policy=fixed_tests)
            self.assertEqual(path[-1]['next_pc'],pc)
            from common import unconditional_transfer
            for step in path:
                row=rows[step['pc']]
                if not unconditional_transfer(row,scenario):
                    self.assertIn(step['test'],fixed_tests(row,scenario))
        self.assertEqual(graph(rows,scenario),baseline)

    def test_test_policy_false_skip_and_loop_pop(self):
        rows=decode(self.mapping)
        scenario=copy.deepcopy(self.scenario)
        # False TSK falls through; false BLT still consumes its stack entry.
        rows[0].update(command=0,unused=False)
        rows[1].update(command=2,unused=False)
        rows[2].update(command=3,unused=False)
        result=graph(rows,scenario,initial_stack=(1025,1),return_sentinel=1025,
                     test_policy=lambda r,s:[0],include_states=True)
        self.assertFalse(result['exceptions'])
        self.assertTrue(result['terminal_return_reached'])
        self.assertEqual(result['reached'],[0,1,2])
        self.assertIn(((1,(1025,1)),(2,(1025,))),result['state_edges'])
        for values in ([],[2]):
            with self.assertRaises(ValueError):
                graph(rows,scenario,test_policy=lambda r,s:values)

    def test_fixed_condition_modes_and_unconditional_override(self):
        from constant_condition_study import fixed_tests
        from analyze import allowed_tests
        scenario=copy.deepcopy(self.scenario)
        row=decode(self.mapping)[0]
        row['select']=3
        scenario['condition']['polarity'][3]=1
        for mode in ('constant','per-select','flags'):
            scenario['condition'].update(mode=mode,value=0,per_select=[0]*8,
                                         sources=['constant']*8)
            self.assertEqual(fixed_tests(row,scenario),[1])
        scenario['condition']['sources'][3]='external'
        scenario['inputs']['external']=1
        self.assertEqual(fixed_tests(row,scenario),[0])
        scenario['condition']['sources'][3]='carry'
        self.assertEqual(fixed_tests(row,scenario),[0,1])
        scenario['condition']['mode']='random'
        self.assertEqual(fixed_tests(row,scenario),[0,1])
        row.update(command=4,select=0,direct=True)
        self.assertEqual(allowed_tests(row,scenario,test_policy=lambda r,s:[0]),[1])

    def test_witness_can_require_empty_stack_at_failure_site(self):
        from context_branch_study import witness
        from unconditional_gate_study import policy_for
        rows=decode(self.mapping)
        scenario=read(HERE/'results/three-bit-gate-study/scenario.json')
        aliases=[r['pc'] for r in rows if r['raw']==rows[0x0fc]['raw']]
        path=witness(rows,scenario,0x220,policy_for(aliases),target_stack=())
        self.assertEqual(path[-1]['next_pc'],0x220)
        self.assertEqual(path[-1]['stack_after'],[])
        self.assertEqual(rows[0x220]['command'],3)
        with self.assertRaises(ValueError):
            witness(rows,scenario,0x220,target_stack=())

    def test_unconditional_brt_gate_preserves_default_and_calls(self):
        from unconditional_gate_study import relaxed_pcs, policy_for
        from common import unconditional_transfer
        from context_branch_study import witness
        rows=decode(self.mapping)
        scenario=read(HERE/'results/third-case-study/scenario-all_cases.json')
        original=copy.deepcopy(rows)
        baseline=graph(rows,scenario)
        pcs=relaxed_pcs(rows,scenario,['!10.6','!11.0'],'or')
        policy=policy_for(pcs)
        for row in rows:
            if row['command']!=6:
                self.assertEqual(policy(row,scenario),unconditional_transfer(row,scenario))
        candidate=graph(rows,scenario,unconditional_policy=policy)
        self.assertFalse(candidate['exceptions'])
        self.assertEqual(set(candidate['reached'])-set(baseline['reached']),
                         {0x287,0x288,0x289,0x28a,0x2d9,0x2da,0x2db,0x3bd,0x3be,0x3bf})
        path=witness(rows,scenario,0x2d9,policy)
        self.assertEqual(path[-1]['next_pc'],0x2d9)
        self.assertTrue(any(s['pc']==0x2d8 and not s['test'] for s in path))
        other=relaxed_pcs(rows,scenario,['10.2','!18.7'],'or')
        combined=graph(rows,scenario,unconditional_policy=policy_for(pcs+other))
        self.assertFalse(combined['exceptions'])
        self.assertEqual(len(combined['reached']),1011)
        self.assertEqual(set(combined['reached'])-set(candidate['reached']),{0x0fa,0x2cf})
        runtime_scenario=copy.deepcopy(scenario)
        runtime_scenario['condition']['brt_unconditional_gate']=dict(
            clauses=[['10.2','!18.7'],['!10.6','!11.0']],
            status='hypothesis',evidence='Test the declared composed gate.')
        self.assertEqual(graph(rows,runtime_scenario),combined)
        self.assertEqual(rows,original)
        self.assertEqual(graph(rows,scenario),baseline)

    def test_runtime_brt_gate_fallthrough_preserves_calls(self):
        mapping=read(HERE/'results/independent-study/variant-2.json')
        scenario=read(HERE/'results/polling-study/immediate-one/scenario.json')
        scenario['initial']=dict(pc=0x0f9,ram=[0]*16,q=0)
        scenario['condition'].update(mode='constant',value=1)
        self.assertEqual(execute(mapping,scenario,1,mode='integrated')['final_state']['pc'],0x28b)
        scenario['condition']['brt_unconditional_gate']=dict(
            clauses=[['10.2','!18.7'],['!10.6','!11.0']],
            status='hypothesis',evidence='Explicit gate fixture.')
        result=execute(mapping,scenario,1,mode='integrated')
        self.assertTrue(result['clean'])
        self.assertEqual(result['final_state']['pc'],0x0fa)
        scenario['initial']['pc']=0x01c
        result=execute(mapping,scenario,1,mode='integrated')
        self.assertTrue(result['clean'])
        self.assertEqual(result['final_state']['pc'],0x01e)

    def test_runtime_brt_gate_rejects_unowned_or_invalid_rules(self):
        for gate in ({},dict(clauses=[['10.2']]),
                     dict(status='hypothesis',evidence='fixture',clauses=[]),
                     dict(status='hypothesis',evidence='fixture',clauses=[[]]),
                     dict(status='hypothesis',evidence='fixture',clauses=[['19.0']])):
            scenario=copy.deepcopy(self.scenario)
            scenario['condition']['brt_unconditional_gate']=gate
            with self.assertRaises(ValueError):validate_scenario(scenario)

    def test_real_statistics_and_loop_entry(self):
        from collections import Counter
        rows=decode(self.mapping)
        self.assertEqual(Counter(r['command'] for r in rows if not r['unused']),{1:639,6:130,3:88,4:87,0:33,5:22,2:22})
        self.assertEqual([r['pc'] for r in rows if r['unused']],[0x1df,0x29f,0x3ff])
        self.assertEqual(len(must_targets(rows)),85)
        self.assertEqual((rows[0x1c]['command'],rows[0x1c]['branch']), (4,0x1e))
        from model import X8X02
        for condition in (0,1):
            seq=X8X02(pc=0x1c);seq.step(4,0x1e,True)
            seq.step(2,test=condition)
            self.assertEqual(seq.pc,0x1d if condition else 0x1f)
            self.assertEqual(seq.pushes,seq.pops)
        self.assertTrue(walk(rows,0x1e9)['balanced'])

    def test_address_search_reproduction(self):
        from common import load
        result=search_address(load(),decode(self.mapping))
        self.assertEqual(result['windows_tested'],2208)
        self.assertEqual(result['chosen_score'],33)
        self.assertEqual(result['best_window_score'],33)
        self.assertEqual(result['refined_score'],33)

    def test_ranked_variants_preserve_alternatives_and_decode(self):
        from common import load
        with tempfile.TemporaryDirectory() as out:
            p=Path(out)
            ranking=rank_layouts(load(),decode(self.mapping),p)
            self.assertGreater(ranking['candidates'],3)
            variants=[read(p/f'datapath-{i}.json') for i in range(1,4)]
            self.assertEqual(variants[0]['ranking']['score'],variants[1]['ranking']['score'])
            self.assertNotEqual(variants[0]['fields']['a'],variants[1]['fields']['a'])
            for mapping in variants:
                self.assertNotEqual(mapping['fields']['a']['bits'],mapping['fields']['b']['bits'])
                self.assertEqual(len(decode(mapping)),1024)
                self.assertIn('operation',decode(mapping)[0])
                self.assertNotIn(4,mapping['fields']['d']['commands'])

    def test_condition_polarity_and_modes(self):
        for name,value in [('command',0),('select',3)]:
            self.mapping['fields'][name]['bits']=value
        self.scenario['condition']['mode']='per-select'
        a=execute(self.mapping,self.scenario,1)
        self.assertEqual(a['final_state']['pc'],1)
        self.scenario['condition']['polarity'][3]=1
        b=execute(self.mapping,self.scenario,1)
        self.assertEqual(b['final_state']['pc'],2)

    def test_bit_order_inversion_and_context(self):
        lanes={c:bytes([0]*1024) for c in ('10','11','17','18')}
        lanes['10']=bytes([128]*1024)
        self.assertEqual(field_value(['10.7','!10.0'],lanes,0),3)
        m=copy.deepcopy(self.mapping)
        m['fields']['d']=dict(bits=['10.'+str(b) for b in range(7,-1,-1)],status='hypothesis',evidence='test',commands=[1])
        self.assertNotIn('d',decode(m,lanes)[0])
        m['fields']['command']['bits']=1
        self.assertEqual(decode(m,lanes)[0]['d'],1)
        m['fields']['command']['bits']=8
        with self.assertRaises(ValueError): validate(m)

    def test_dispatch_bounds_and_missing_site(self):
        self.scenario['dispatch']['tables']['126']['base']=1023
        with self.assertRaises(ValueError): validate_scenario(self.scenario)
        self.scenario=read(HERE/'baseline.json')
        del self.scenario['dispatch']['tables']['126']
        with self.assertRaisesRegex(ValueError,'missing dispatch'): execute(self.mapping,self.scenario,1)

    def test_seed_replay_and_bounded_trace(self):
        with tempfile.TemporaryDirectory() as out:
            a=execute(self.mapping,self.scenario,2000,12,out=out,trace_limit=7)
            b=execute(self.mapping,self.scenario,2000,12,trace_limit=7)
            self.assertEqual(a,b)
            self.assertEqual(len((Path(out)/'trace.jsonl').read_text().splitlines()),7)
            self.assertEqual(a['completed_cycles'],2000)
            self.assertEqual(a['stack']['overflows'],0)

    def test_indirect_branch_policy(self):
        for name,value in [('command',6),('direct',0),('select',0)]:
            self.mapping['fields'][name]['bits']=value
        self.scenario['condition'].update(mode='constant',value=1)
        self.scenario['indirect_branch'].update(source='constant',value=123)
        result=execute(self.mapping,self.scenario,1)
        self.assertEqual(result['final_state']['pc'],123)
        self.assertEqual(result['assumption_counts']['indirect BRT stub'],1)

    def test_stack_failures_not_repaired(self):
        self.mapping['fields']['command']['bits']=3
        a=execute(self.mapping,self.scenario,10)
        self.assertFalse(a['clean']);self.assertEqual(a['completed_cycles'],0)
        self.assertEqual(a['stack']['underflows'],1)
        self.mapping['fields']['command']['bits']=5
        a=execute(self.mapping,self.scenario,10)
        self.assertEqual(a['stack']['overflows'],6)
        self.assertEqual(a['completed_cycles'],10)
        self.assertFalse(a['clean'])

    def test_flag_fallback_io_and_initial_state(self):
        m=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,select=3,i=7|(3<<3)|(3<<6),a=0,b=0,d=9).items():
            m['fields'][name]=dict(bits=bits,status='stub',evidence='test fixture')
        s=self.scenario;s['condition']['mode']='flags'
        s['io']['read'].update(mode='table',table=[12,34])
        s['io']['writes']=[dict(pc=0,address=17,source='y',status='hypothesis',evidence='test')]
        with tempfile.TemporaryDirectory() as out:
            a=execute(m,s,3,mode='integrated',out=out)
            self.assertEqual(a['assumption_counts']['unknown carry'],3)
            self.assertEqual(a['final_state']['ram'][0],34)
            import json
            event=json.loads((Path(out)/'io.jsonl').read_text())
            self.assertEqual((event['address'],event['value']),(17,34))

    def test_branch_table_dispatch_does_not_push_stack(self):
        scenario=read(HERE/'branch-tables.json')
        scenario['initial']['pc']=0x109
        scenario['dispatch'].update(mode='sequence',sequence=[2])
        scenario['condition']['polarity'][0]=1
        result=execute(self.mapping,scenario,1)
        self.assertEqual(result['final_state']['pc'],0x10c)
        self.assertEqual(result['stack']['writes'],0)
        self.assertEqual(result['stack']['final_depth'],0)
        self.assertEqual(result['dispatch_counts'],{0x109:1})
        self.assertEqual(result['assumption_counts']['unconditional computed transfer'],1)

    def test_local_branch_table_evidence_and_graph(self):
        scenario=read(HERE/'branch-tables.json');rows=decode(self.mapping)
        for site,table in scenario['branch_tables'].items():
            for i in range(table['count']):
                row=rows[table['base']+i*table['stride']]
                self.assertEqual((row['command'],row['select'],row['direct']),(6,0,1))
        baseline=graph(rows,self.scenario);expanded=graph(rows,scenario)
        self.assertEqual(len(baseline['reached']),338)
        self.assertEqual(len(expanded['reached']),682)
        self.assertEqual(expanded['exceptions'],[])
        self.assertIn((0x109,0x111,'branch-dispatch:hypothesis'),expanded['edges'])
        scenario['branch_tables']['0']=scenario['branch_tables']['265']
        with self.assertRaisesRegex(ValueError,'site must be BRT'):
            execute(self.mapping,scenario,1)

    def test_second_register_field_has_unique_training_match(self):
        from common import load
        result=recover_register(load(),self.mapping,read(HERE/'register-search.json'))
        self.assertEqual(result['candidates'],1184)
        self.assertEqual(result['best'],dict(bits=['11.4','11.3','11.2','11.1'],score=48))
        self.assertEqual(len(result['tied_best']),1)
        self.assertEqual(result['selector_table']['source_values'],[0]*16)
        self.assertEqual(result['selector_table']['other_values'],list(range(16)))
        for table in result['heldout']:
            self.assertEqual(set(table['source_values']),{10,11,12,13})

    def test_constrained_variants_keep_instruction_and_register_bits_disjoint(self):
        for i in range(1,4):
            mapping=read(HERE/f'results/register-study/variant-{i}.json')
            fields={k:{b.lstrip('!') for b in mapping['fields'][k]['bits']} for k in ('i','a','b')}
            self.assertFalse(fields['i']&(fields['a']|fields['b']))
            self.assertFalse(fields['a']&fields['b'])
            self.assertEqual(len(fields['i']),9)

    def test_table_equivalence_is_a_real_datapath_limitation(self):
        from common import load
        from model import Am2901
        mapping=read(HERE/'results/register-study/variant-1.json')
        report=table_semantics(mapping,load(),read(HERE/'register-search.json'))
        self.assertEqual(report['families'][0]['equivalent_entry_groups'],[[0,1,2,3]])
        rows=decode(mapping)
        for seed in (0,1,37,255):
            outcomes=[]
            for entry in range(4):
                cpu=Am2901(ram=[(i*19+seed)&255 for i in range(16)],q=seed)
                outputs=[]
                for row in rows[0x379+4*entry:0x37d+4*entry]:
                    outputs.append(cpu.step(row['i'],row['a'],row['b'],row['d']))
                outcomes.append((cpu.ram,cpu.q,outputs))
            self.assertTrue(all(x==outcomes[0] for x in outcomes))

    def test_mapped_carry_propagation_and_unknown_fallback(self):
        from model import Am2901
        policy=dict(initial=0,unknown=1,select_field='feedback',constant_field='constant')
        carry=CarryInput(policy)
        cpu=Am2901(ram=[0,1]+[0]*14,q=0)
        # Negate 0x0100: low zero produces carry, making the high byte 0xff.
        instruction=0|(1<<3)|(3<<6)
        low=cpu.step(instruction,0,2,0,carry.resolve(dict(feedback=0,constant=1)))
        carry.observe(low)
        high=cpu.step(instruction,1,3,0,carry.resolve(dict(feedback=1,constant=0)))
        self.assertEqual((low['f'],high['f']),(0,255))
        carry.observe(dict(carry=None))
        self.assertEqual(carry.resolve(dict(feedback=1,constant=0)),1)
        self.assertEqual(carry.counts['unknown_feedback'],1)
        self.assertIsNone(carry.previous)
        constant=CarryInput(0);constant.observe(dict(carry=1))
        self.assertEqual(constant.resolve({}),0)

    def test_rotation_tables_and_overlapping_register_counterexample(self):
        from rotation_study import fixtures
        config=read(HERE/'rotation-search.json')
        for index in range(1,4):
            mapping=read(HERE/f'results/rotation-study/variant-{index}.json')
            fields={k:{b.lstrip('!') for b in mapping['fields'][k]['bits']} for k in ('i','a','b')}
            self.assertFalse(fields['i']&(fields['a']|fields['b']))
            report=fixtures(mapping,config)
            self.assertEqual(report['failures'],[])
            self.assertEqual(report['rotation_checks'],312)
            self.assertEqual(report['virtual_output_checks'],468)
            # In-place bank 12 overwrites Y with X before the second copy.
            self.assertEqual(report['alias_table'][0]['output'],(0x1234,0x1234))
            self.assertNotEqual(report['alias_table'][0]['output'],(0x1234,0x5678))

    def test_feedback_scenario_requires_datapath_and_one_bit_fields(self):
        mapping=read(HERE/'results/rotation-study/variant-1.json')
        scenario=read(HERE/'results/rotation-study/scenario-1.json')
        with self.assertRaisesRegex(ValueError,'integrated mode'):
            execute(mapping,scenario,1)
        mapping['fields']['carry']['bits']=2
        with self.assertRaises(ValueError):
            execute(mapping,scenario,1,mode='integrated')

    def test_caller_state_reconstruction_preserves_timing(self):
        from caller_study import inspect_trace
        scenario=copy.deepcopy(self.scenario)
        scenario['dispatch']['tables']={'10':dict(targets=[100,120,130,150])}
        records=[dict(cycle=0,pc=9,registers={'10':7},q=5,alu=dict(y=6),dispatch_entry=None),
                 dict(cycle=1,pc=10,registers={'10':8},q=9,alu=dict(y=3),dispatch_entry=2,next_pc=100)]
        sample=inspect_trace(records,scenario)[0]
        self.assertEqual(sample['ram_before'][10],7)
        self.assertEqual(sample['ram_at_entry'][10],8)
        self.assertEqual((sample['q_before'],sample['q_at_entry']),(5,9))
        self.assertEqual(sample['candidate_indices'],dict(current_y=3,q=1,previous_y=2))
        self.assertEqual(scenario['initial']['ram'][10],0)
        with self.assertRaisesRegex(ValueError,'contiguous'):
            inspect_trace(records[1:],scenario)

    def test_nonzero_q_caller_breaks_simple_rotation(self):
        from caller_study import check_rotation
        mapping=read(HERE/'results/rotation-study/variant-1.json')
        scenario=read(HERE/'results/rotation-study/scenario-1.json')
        sample=dict(site=0x3d7,entry=1,q_at_entry=1,ram_at_entry=[0]*12+[1,1,0,0])
        bases=read(HERE/'rotation-search.json')['rotation_table_bases']
        check_rotation(sample,decode(mapping),scenario,bases)
        self.assertEqual(sample['rotation_check'],dict(expected=(0xfeff,0),actual=(0,0x101),matches=False))
        sample['q_at_entry']=0
        check_rotation(sample,decode(mapping),scenario,bases)
        self.assertTrue(sample['rotation_check']['matches'])

    def test_separated_source_candidates_and_q_shift_loop(self):
        from common import load
        from independent_study import search_sources, arithmetic
        from model import Am2901, X8X02
        config=read(HERE/'independent-search.json');base=read(HERE/'rotation-search.json')
        candidates=search_sources(load(),config,base)
        self.assertEqual(len(candidates),4)
        for index,source in enumerate(candidates,1):
            mapping=read(HERE/f'results/independent-study/variant-{index}.json')
            self.assertEqual(mapping['fields']['i']['bits'][:3],source)
            self.assertEqual(arithmetic(mapping,config,base)['failures'],[])
            rows=decode(mapping)
            for initial_q in range(256):
                cpu=Am2901(q=initial_q)
                seq=X8X02(pc=0x123);seq.step(4,0x1e9,True)
                iterations=0
                while seq.pc!=0x1eb:
                    row=rows[seq.pc]
                    result=cpu.step(row['i'],row['a'],row['b'],0x55,0)
                    seq.step(row['command'],row['branch'],not result['zero'])
                    if row['pc']==0x1e9:iterations+=1
                    self.assertLessEqual(iterations,8)
                self.assertEqual(cpu.q,0)
                self.assertEqual(iterations,max(1,initial_q.bit_length()))
                self.assertEqual(cpu.ram[0],0)
                seq.step(3)
                self.assertEqual(seq.pc,0x124)
                self.assertEqual(seq.pushes,seq.pops)

    def test_random_flag_sources_preserve_seeded_random_behavior(self):
        mapping=read(HERE/'results/independent-study/variant-2.json')
        scenario=read(HERE/'results/independent-study/scenario-2.json')
        hybrid=copy.deepcopy(scenario)
        hybrid['condition'].update(mode='flags',sources=['random']*8)
        for seed in (0,11,31):
            old=execute(mapping,scenario,1000,seed,'integrated',trace_limit=0)
            new=execute(mapping,hybrid,1000,seed,'integrated',trace_limit=0)
            self.assertEqual(old['trace_digest'],new['trace_digest'])
            self.assertEqual(old['final_state'],new['final_state'])
            self.assertEqual(old['address_counts'],new['address_counts'])
        hybrid['condition']['sources'][0]='unrecognized'
        with self.assertRaisesRegex(ValueError,'condition sources'):
            validate_scenario(hybrid)

    def test_select_zero_flag_does_not_override_unconditional_calls(self):
        from condition_study import scenario_for
        mapping=read(HERE/'results/independent-study/variant-2.json')
        base=read(HERE/'results/independent-study/scenario-2.json')
        scenario=scenario_for(base,read(HERE/'condition-search.json'),'current',0)
        rows=decode(mapping)
        # Zero ALU output, but a select-zero direct BSR must still push and call.
        rows[0].update(command=4,select=0,direct=1,branch=10,i=7|(1<<6),a=0,b=0)
        with patch('execute.decode',return_value=rows):
            result=execute(mapping,scenario,1,mode='integrated')
        self.assertEqual(result['final_state']['pc'],10)
        self.assertEqual(result['stack']['final_depth'],1)
        rows[0]['command']=0
        with patch('execute.decode',return_value=rows):
            result=execute(mapping,scenario,1,mode='integrated')
        self.assertEqual(result['final_state']['pc'],1)
        self.assertEqual(result['stack']['final_depth'],0)

    def test_sparse_dispatch_targets_and_validation(self):
        from common import table_targets
        self.assertEqual(table_targets(dict(base=10,count=3,stride=4)),[10,14,18])
        self.assertEqual(table_targets(dict(targets=[10,37,100])),[10,37,100])
        for table in ({'targets':[]},{'targets':[1,1]},{'targets':[1024]},
                      {'targets':[True]},{'targets':[1],'base':0},{'base':0,'count':0,'stride':1}):
            with self.assertRaises(ValueError):table_targets(table)
        scenario=read(HERE/'branch-tables.json')
        table=dict(targets=[0x11a,0x133,0x345],status='hypothesis',evidence='sparse fixture')
        scenario['branch_tables'][str(0x109)]=table
        scenario['initial']['pc']=0x109
        scenario['dispatch'].update(mode='sequence',sequence=[1])
        result=execute(self.mapping,scenario,1)
        self.assertEqual(result['final_state']['pc'],0x133)
        self.assertEqual(result['stack']['writes'],0)
        scenario['initial']['pc']=0x81
        scenario['dispatch']['tables'][str(0x81)]=table
        result=execute(self.mapping,scenario,1)
        self.assertEqual(result['final_state']['pc'],0x133)
        self.assertEqual(result['stack']['writes'],1)
        g=graph(decode(self.mapping),scenario)
        self.assertIn((0x81,0x345,'dispatch:hypothesis'),g['edges'])

    def test_low_address_handler_boundaries_and_stack_graph(self):
        from handler_study import boundaries,scenarios
        config=read(HERE/'handler-search.json');base=read(HERE/'branch-tables.json')
        rows=decode(self.mapping);evidence=boundaries(rows,base,config)
        self.assertEqual(evidence['handlers'],[0x009,0x00d,0x013,0x022,0x032,0x03a,0x054])
        self.assertIn(0x03f,evidence['deferred'])
        alternatives,scenario=scenarios(base,config,evidence)
        g=graph(rows,scenario)
        self.assertEqual(len(g['reached']),775)
        self.assertEqual(g['exceptions'],[])
        self.assertIn((0x008,0x013,'branch-dispatch:hypothesis'),g['edges'])
        self.assertIn((0x036,0x039,'branch-dispatch:hypothesis'),g['edges'])
        self.assertNotIn(0x03f,g['reached'])
        self.assertIn(0x03f,graph(rows,alternatives['third-entry-ablation'])['reached'])

    def test_explicit_call_table_overrides_direct_hint_and_returns(self):
        from exception_study import scenarios
        config=read(HERE/'exception-call.json')
        scenario=scenarios(read(HERE/'results/handler-study/scenario.json'),config)['local_table']
        scenario['initial']['pc']=config['call_site']
        scenario['dispatch'].update(mode='sequence',sequence=[2])
        self.assertEqual(decode(self.mapping)[config['call_site']]['direct'],1)
        one=execute(self.mapping,scenario,1)
        self.assertEqual(one['final_state']['pc'],0x1e7)
        self.assertEqual(one['stack']['final_depth'],1)
        two=execute(self.mapping,scenario,2)
        self.assertEqual(two['final_state']['pc'],0x1a3)
        self.assertEqual(two['stack']['final_depth'],0)
        # A configured target does not make a conditional call unconditional.
        rows=decode(self.mapping);rows[config['call_site']]['select']=1
        scenario['condition'].update(mode='constant',value=0)
        with patch('execute.decode',return_value=rows):
            skipped=execute(self.mapping,scenario,1)
        self.assertEqual(skipped['final_state']['pc'],0x1a3)
        self.assertEqual(skipped['stack']['writes'],0)

    def test_exceptional_call_and_local_pop_group_evidence(self):
        from exception_study import evidence,scenarios
        config=read(HERE/'exception-call.json')
        mapping=read(HERE/'results/independent-study/variant-2.json')
        report=evidence(decode(mapping),config)
        self.assertEqual(report['non_no_load_calls'],[0x07e,0x1a2])
        self.assertIn([0x1e5,0x1e6,0x1e7,0x1e8],report['isolated_pop_groups'])
        alternatives=scenarios(read(HERE/'results/handler-study/scenario.json'),config)
        baseline=graph(decode(self.mapping),alternatives['baseline'])
        candidate=graph(decode(self.mapping),alternatives['local_table'])
        self.assertNotIn(0x1a3,baseline['reached'])
        self.assertIn(0x1a3,candidate['reached'])
        self.assertEqual(len(candidate['reached']),841)
        self.assertEqual(candidate['exceptions'],[])
        self.assertIn((0x1a2,0x1e8,'dispatch:hypothesis'),candidate['edges'])

    def test_exception_table_uses_preceding_carry(self):
        from exception_study import table_examples
        config=read(HERE/'exception-call.json')
        mapping=read(HERE/'results/independent-study/variant-2.json')
        scenario=read(HERE/'results/independent-study/scenario-2.json')
        examples=table_examples(decode(mapping),scenario['inputs']['carry'],config)
        self.assertEqual([r['ram_b'] for r in examples[0]['outputs']],[251,10,3,3])
        self.assertEqual([r['ram_b'] for r in examples[1]['outputs']],[252,11,4,4])
        self.assertEqual([r['carry_in'] for r in examples[0]['outputs']],[0]*4)
        self.assertEqual([r['carry_in'] for r in examples[1]['outputs']],[1]*4)

    def test_local_graph_probe_distinguishes_return_from_terminal_loop(self):
        rows=decode(self.mapping)
        rows[5].update(command=3,unused=False)
        rows[6].update(command=6,select=0,direct=1,branch=6,unused=False)
        without=graph(rows,self.scenario,start=5)
        self.assertEqual(without['exceptions'],['005: possible stack underflow'])
        returning=graph(rows,self.scenario,start=5,initial_stack=(-1,),return_sentinel=-1)
        self.assertTrue(returning['terminal_return_reached'])
        self.assertEqual(returning['reached'],[5])
        self.assertEqual(returning['exceptions'],[])
        looping=graph(rows,self.scenario,start=6,initial_stack=(-1,),return_sentinel=-1)
        self.assertFalse(looping['terminal_return_reached'])
        self.assertEqual(looping['reached'],[6])
        with self.assertRaises(ValueError):graph(rows,self.scenario,return_sentinel=5)
        with self.assertRaises(ValueError):graph(rows,self.scenario,initial_stack=(-1,))

    def test_structural_target_pools_reject_overflowing_combinations(self):
        from target_study import classify,scenarios
        config=read(HERE/'target-pools.json')
        base=read(HERE/'results/exception-study/scenario-local_table.json')
        rows=decode(self.mapping);classification=classify(rows,base,config)
        self.assertTrue(classification['setup_equal'])
        entries={r['entry']:r for r in classification['entries']}
        self.assertTrue(entries[0x200]['root_safe'])
        self.assertFalse(entries[0x200]['returns'])
        self.assertFalse(entries[0x22b]['root_safe'])
        self.assertTrue(entries[0x22b]['returns'])
        self.assertTrue(entries[0x22b]['leaf'])
        alternatives,excluded=scenarios(base,config,classification)
        self.assertIn(0x2df,excluded[str(0x21f)])
        self.assertIn(0x2bc,excluded[str(0x2c4)])
        self.assertTrue(graph(rows,alternatives['unrestricted'])['exceptions'])
        bounded=graph(rows,alternatives['bounded'])
        self.assertEqual(bounded['exceptions'],[])
        self.assertEqual(len(bounded['reached']),1004)
        self.assertEqual(alternatives['bounded']['dispatch']['tables'][str(0x2c4)]['targets'],[0x22b,0x22c,0x22d,0x2b3])

    def test_rom_dispatch_preserves_bytes_indices_and_repeated_targets(self):
        from rom_study import load_rom,rom_table,scenarios,reconstruct_lookups
        from common import table_targets
        config=read(HERE/'rom-dispatch.json');data=load_rom(config)
        table=rom_table(data,config['branch_lookups'][str(0x26f)],config)
        self.assertEqual(len(table_targets(table)),16)
        self.assertEqual(table_targets(table)[:3],[0x2c6]*3)
        bad=copy.deepcopy(table);bad['allow_duplicate_targets']=False
        with self.assertRaises(ValueError):table_targets(bad)
        bad['allow_duplicate_targets']='yes'
        with self.assertRaises(ValueError):table_targets(bad)
        base=read(HERE/'results/target-study/scenario-bounded.json')
        scenario=scenarios(base,data,config)['rom_calls']
        self.assertEqual(scenario['branch_tables']['8']['targets'],[9,15,11,19,34,13,50,84])
        scenario['initial']['pc']=8
        scenario['dispatch'].update(mode='sequence',sequence=[1])
        result=execute(self.mapping,scenario,1)
        self.assertEqual(result['final_state']['pc'],15)
        self.assertEqual(result['stack']['writes'],0)
        records=[dict(cycle=0,pc=8,command=6,dispatch_entry=1,next_pc=15)]
        lookup=reconstruct_lookups(records,scenario,data)[0]
        self.assertEqual((lookup['rom_address'],lookup['rom_value'],lookup['target']),(0xe1,15,15))
        records[0]['next_pc']=13
        with self.assertRaisesRegex(ValueError,'reproduce executed target'):
            reconstruct_lookups(records,scenario,data)
        bad_config=dict(config,rom_sha256='wrong')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):load_rom(bad_config)

    def test_previous_y_index_uses_preceding_output_and_explicit_initial_value(self):
        mapping=read(HERE/'results/independent-study/variant-2.json')
        scenario=read(HERE/'results/independent-study/scenario-2.json')
        scenario['inputs']['carry']=0
        scenario['io']['read']['mode']='immediate'
        scenario['branch_tables']['1']=dict(targets=[10,20,30,40],index_source='previous_y',
            status='hypothesis',evidence='retained-output fixture')
        scenario['dispatch']['initial_y']=2
        rows=decode(mapping)
        rows[0].update(command=1,i=7|(1<<6),d=3)
        rows[1].update(command=6,select=0,direct=1,i=7|(1<<6),d=1)
        with patch('execute.decode',return_value=rows):
            result=execute(mapping,scenario,2,mode='integrated')
        self.assertEqual(result['final_state']['pc'],40)
        self.assertEqual(result['final_state']['previous_y'],1)
        scenario['initial']['pc']=1
        with patch('execute.decode',return_value=rows):
            first=execute(mapping,scenario,1,mode='integrated')
        self.assertEqual(first['final_state']['pc'],30)
        scenario['branch_tables']['1']['index_source']='y'
        with patch('execute.decode',return_value=rows):
            current=execute(mapping,scenario,1,mode='integrated')
        self.assertEqual(current['final_state']['pc'],20)
        scenario['branch_tables']['1']['index_source']='previous_y'
        del scenario['dispatch']['initial_y']
        with self.assertRaisesRegex(ValueError,'explicit initial_y'):validate_scenario(scenario)
        scenario['dispatch']['initial_y']=0
        with self.assertRaisesRegex(ValueError,'integrated mode'):execute(mapping,scenario,1)

    def test_masked_datapath_nested_dispatch_from_reset(self):
        from masked_nested_dispatch import scenario_for, inspect, check_mask
        from defined_condition_fit import load_trace
        config=read(HERE/'masked-nested-dispatch.json')
        mapping=read(HERE/config['mapping']);rows=decode(mapping)
        self.assertEqual(check_mask(rows,0xf3,0x55),0x51)
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            for mask in (81,163,245):
                for outer,inner in (('q','q'),('previous_y','q'),('y','q'),('q','y')):
                    scenario=scenario_for(config,mask,255,outer,inner)
                    result=execute(mapping,scenario,512,seed=115,mode='integrated',out=out,trace_limit=512)
                    self.assertTrue(result['clean'])
                    events=inspect(load_trace(out),scenario,mask)
                    nested=[e for e in events if e['pc']==0x2bc]
                    self.assertEqual(bool(nested),outer!='y')
                    if nested:
                        self.assertEqual(nested[0]['before']['q'],mask)
                        self.assertEqual(result['stack']['max_depth'],4)
                        call=next(e for e in events if e['pc']==0x2c4)
                        self.assertEqual(call['next_pc'],0x2b3 if inner=='y' else 0x22b if mask==81 else 0x225)

    def test_tail_call_stack_contract_and_q3_difference_guard(self):
        from tail_stack_contract import guard, constant_tests, replay
        config=read(HERE/'tail-stack-contract.json')
        rows=decode(read(HERE/config['mapping']));scenario=read(HERE/config['scenario'])
        for depth in range(5):
            result=graph(rows,scenario,start=0x2fd,initial_stack=(1024,)*depth,return_sentinel=1024)
            self.assertEqual(not result['exceptions'],depth==1)
        for r0 in range(256):
            self.assertEqual(guard(rows,r0,(r0+1)&255),0)
            self.assertEqual(guard(rows,r0,r0),1)
        bad=copy.deepcopy(rows);bad[0x3bb]['carry']=1
        with self.assertRaises(AssertionError):guard(bad,0,1)
        condition=read(HERE/config['condition_scenario'])['condition']
        self.assertEqual(constant_tests(condition)(rows[0x2e3],scenario),[0])
        failed=replay(HERE/config['witnesses']['empty_entry'])
        self.assertFalse(failed['clean'])
        self.assertEqual(failed['stop'],'unknown stack at PC 2ff')

    def test_default_gap_policy_explanations_and_unsafe_complete_graph(self):
        from reset_witness_catalog import build_catalog
        from entry_policy_audit import relaxed_graph
        catalog=build_catalog()
        self.assertEqual(len(catalog['entries']),22)
        for visits in catalog['entries'].values():
            for visit in visits:
                explanation=visit['entry_policy']
                self.assertTrue(explanation['forced_jump_fallthroughs'])
                self.assertEqual(explanation['path'][0],explanation['root_pc'])
                for branch in explanation['forced_jump_fallthroughs']:
                    self.assertEqual(int(branch['actual_target'],16),int(branch['pc'],16)+1)
        explanation=catalog['entries']['2DF'][0]['entry_policy']
        self.assertEqual(explanation['root_pc'],'2D8')
        self.assertEqual([b['pc'] for b in explanation['forced_jump_fallthroughs']],['2D8','2DB','2DE'])
        rows=decode(read(HERE/'sequencer.json'))
        scenario=read(HERE/catalog['configuration']['baseline_scenario'])
        sites={0x0f9,0x0fc,0x255,0x257,0x2ce,0x2de,0x3bc}
        relaxed=relaxed_graph(rows,scenario,sites)
        self.assertEqual(len(relaxed['reached']),1021)
        self.assertIn('2ff: possible stack underflow',relaxed['exceptions'])
        for pc in sites:self.assertLess(len(relaxed_graph(rows,scenario,sites-{pc})['reached']),1021)
        self.assertEqual(len(graph(rows,scenario)['reached']),999)

    def test_rom_carry_reply_recurrence_and_y_dependency(self):
        from rom_carry_replies import transition, predict, check_step
        from rom_gate_handlers import scenario_for_gate, outcome
        from rom_study import load_rom
        from defined_condition_fit import load_trace
        config=read(HERE/'rom-carry-replies.json');table=load_rom(config)[256:]
        mapping=read(HERE/config['profiles']['q3']);rows=decode(mapping)
        pcs=read(HERE/config['gates'])['fits'][0]['pcs']
        scenario=scenario_for_gate(config,5,pcs)
        for d,n in ((0,1),(2,2),(251,13)):
            self.assertEqual(predict(table,d)['iterations'],n)
        for d,period in ((1,1),(249,15),(255,11)):
            self.assertEqual(predict(table,d)['period'],period)
        for x in (0,1,64,127,255):
            for d in (0,1,2,119,249,251,255):check_step(rows,scenario,table,x,d)
        corrupted=copy.deepcopy(rows);corrupted[0x36e]['i']+=64
        with self.assertRaises(AssertionError):check_step(corrupted,scenario,table,0,1)
        with tempfile.TemporaryDirectory() as temporary:
            for d in (249,251):
                scenario['io']['read']['pc_sequences'][str(0x36d)]=[d]
                result=execute(mapping,scenario,512,mode='integrated',out=Path(temporary),trace_limit=512)
                finding=outcome(load_trace(Path(temporary)),result,scenario)
                self.assertTrue(finding['clean'])
                if d==249:self.assertEqual(finding['repeat']['period'],45)
                else:self.assertEqual(finding['first_terminal'],146)

    def test_rom_gate_handler_transfer_and_delayed_release(self):
        from rom_gate_handlers import scenario_for_gate, outcome
        from defined_condition_fit import load_trace
        config=read(HERE/'rom-gate-handlers.json')
        fits=read(HERE/'results/rom-gate-study/report.json')['fits']
        mapping=read(HERE/config['profiles']['q3'])
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            for gate,expected in ((None,'terminal'),(0,'repeat'),(50,'terminal')):
                scenario=scenario_for_gate(config,5,None if gate is None else fits[gate]['pcs'])
                result=execute(mapping,scenario,512,mode='integrated',out=out,trace_limit=512)
                trace=load_trace(out);finding=outcome(trace,result,scenario)
                self.assertEqual(finding['outcome'],expected)
                self.assertIn('previous_y',finding['final_state'])
                if gate==0:
                    self.assertEqual(finding['repeat']['period'],3)
                    for row in trace:
                        if row['pc']==0x36c:
                            self.assertEqual((row['external_read']['address'],row['external_read']['value']),(0x100,0))
                        if row['pc']==0x36e:
                            self.assertEqual((row['alu']['f'],row['alu']['y'],row['test']),(1,0,1))
            for delay in (0,1,7):
                scenario=scenario_for_gate(config,5,fits[0]['pcs'],delay)
                result=execute(mapping,scenario,512,mode='integrated',out=out,trace_limit=512)
                finding=outcome(load_trace(out),result,scenario)
                self.assertTrue(finding['clean'])
                self.assertEqual(finding['first_terminal'],110+3*delay)

    def test_rom_gate_fit_and_global_read_effects(self):
        from common import load
        from rom_gate_study import search, observe
        from sine_operand_study import scenario_for_phase
        from rom_study import load_rom
        from defined_condition_fit import load_trace
        config=read(HERE/'rom-gate-study.json')
        tested,fits=search(config,load())
        self.assertEqual(tested,41728)
        small=[f for f in fits if len(f['terms'])<=2]
        self.assertEqual(len(small),1)
        self.assertEqual(small[0]['terms'],[('11.4',0),('18.5',0)])
        self.assertEqual(len(small[0]['pcs']),433)
        self.assertEqual(len(fits),137)
        scenario=scenario_for_phase(config,'q3',32)
        scenario['io']['read']['address']['pcs']=small[0]['pcs']
        with tempfile.TemporaryDirectory() as temporary:
            result=execute(read(HERE/config['profiles']['q3']),scenario,160,
                mode='integrated',out=Path(temporary),trace_limit=160)
            finding=observe(load_trace(Path(temporary)),result,load_rom(config),32)
        self.assertTrue(finding['clean'] and finding['output_matches'])
        self.assertEqual(finding['first_terminal'],110)
        self.assertEqual([(r['pc'],r['address'],r['value']) for r in finding['selected_rom_reads']],
                         [(0x115,0x106,19),(0x115,0x106,19),(0x317,0x120,90),(0x36c,0x100,0)])
        # Asking the same raw word to be both external and ROM is inconsistent.
        contradictory=copy.deepcopy(config);contradictory['negative'].append(0x317)
        self.assertEqual(search(contradictory,load())[1],[])

    def test_rom_feedback_at_selected_pcs_preserves_external_sequences(self):
        from defined_condition_fit import load_trace
        mapping=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,i=7|(1<<6),a=0,b=0,d=0).items():
            mapping['fields'][name]=dict(bits=bits,status='stub',evidence='mixed read fixture')
        scenario=copy.deepcopy(self.scenario)
        scenario['io']['read'].update(mode='pc_sequence',pc_sequences={'0':[1],'2':[17]},
            sequence_end='hold-last',status='stub',evidence='mixed read fixture',
            expected_sha256=read(HERE/'feedback-search.json')['rom_sha256'],
            address=dict(source='previous_y',bank=0,initial_y=0,pcs=[1],status='hypothesis',evidence='fixture'))
        with tempfile.TemporaryDirectory() as temporary:
            result=execute(mapping,scenario,3,mode='integrated',out=Path(temporary),trace_limit=3)
            trace=load_trace(Path(temporary))
        self.assertEqual([r['alu']['y'] for r in trace],[1,49,17])
        self.assertEqual(result['rom_reads']['address_counts'],{1:1})
        self.assertEqual(result['rom_reads']['selected_by_alu'],1)
        self.assertEqual(result['read_sequence_visits'],{0:1,2:1})
        self.assertNotIn('address',trace[0]['external_read'])
        self.assertEqual(trace[1]['external_read']['address'],1)
        self.assertNotIn('address',trace[2]['external_read'])
        for pcs in ([],[1,1],[True],[-1],[1024],[0]):
            bad=copy.deepcopy(scenario);bad['io']['read']['address']['pcs']=pcs
            with self.assertRaisesRegex(ValueError,'ROM read sites'):validate_scenario(bad)
        bad=copy.deepcopy(scenario);bad['io']['read']['expected_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):execute(mapping,bad,3,mode='integrated')
        with self.assertRaisesRegex(ValueError,'integrated mode'):execute(mapping,scenario,3)

    def test_sine_rom_operand_reaches_nonzero_arithmetic_from_reset(self):
        from sine_operand_study import scenario_for_phase, inspect_phase
        from rom_study import load_rom
        from defined_condition_fit import load_trace
        config=read(HERE/'sine-operand-study.json');rom=load_rom(config)
        with tempfile.TemporaryDirectory() as temporary:
            for profile in ('q1','q3'):
                for phase in (0,32,64):
                    scenario=scenario_for_phase(config,profile,phase)
                    result=execute(read(HERE/config['profiles'][profile]),scenario,160,
                        mode='integrated',out=Path(temporary),trace_limit=160)
                    self.assertTrue(result['clean'])
                    finding=inspect_phase(load_trace(Path(temporary)),scenario,profile,phase,rom)
                    self.assertEqual(finding['expected_pairs'][0],2*(5+rom[256+phase]) if profile=='q3' else 0)
                    self.assertEqual(finding['first_terminal'],110)

    def test_rom_feedback_can_select_a_bank_at_each_read_site(self):
        from defined_condition_fit import load_trace
        mapping=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,i=7|(1<<6),a=0,b=0,d=0).items():
            mapping['fields'][name]=dict(bits=bits,status='stub',evidence='bank fixture')
        scenario=copy.deepcopy(self.scenario)
        scenario['io']['read'].update(mode='pc_sequence',pc_sequences={'0':[1]},
            sequence_end='hold-last',status='stub',evidence='bank fixture',
            expected_sha256=read(HERE/'feedback-search.json')['rom_sha256'],
            address=dict(source='previous_y',bank=0,bank_by_pc={'2':256},
                         initial_y=0,pcs=[1,2],status='hypothesis',
                         evidence='alternative A8 selection at PC 2'))
        with tempfile.TemporaryDirectory() as temporary:
            result=execute(mapping,scenario,3,mode='integrated',out=Path(temporary),trace_limit=3)
            trace=load_trace(Path(temporary))
        rom=(HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin').read_bytes()
        self.assertEqual([r['external_read']['address'] for r in trace[1:]],
                         [1,256+rom[1]])
        self.assertEqual([r['external_read']['value'] for r in trace[1:]],
                         [rom[1],rom[256+rom[1]]])
        self.assertEqual(result['rom_reads']['selected_by_alu'],2)
        for overrides in ({'0':256},{'2':1},{'2':True},{'bad':0}):
            bad=copy.deepcopy(scenario)
            bad['io']['read']['address']['bank_by_pc']=overrides
            with self.assertRaisesRegex(ValueError,'ROM bank overrides'):
                validate_scenario(bad)

    def test_alu_rom_feedback_reads_prior_output_and_records_consumption(self):
        import json
        mapping=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,i=7|(1<<6),a=0,b=0,d=0).items():
            mapping['fields'][name]=dict(bits=bits,status='stub',evidence='ROM feedback fixture')
        config=read(HERE/'feedback-search.json')
        scenario=copy.deepcopy(self.scenario)
        scenario['io']['read'].update(mode='am27s31',expected_sha256=config['rom_sha256'],
            address=dict(source='previous_y',bank=0,initial_y=1,status='hypothesis',evidence='fixture'))
        with tempfile.TemporaryDirectory() as out:
            result=execute(mapping,scenario,3,mode='integrated',out=out,trace_limit=3)
            records=[json.loads(line) for line in (Path(out)/'trace.jsonl').read_text().splitlines()]
        self.assertEqual([(r['external_read']['address'],r['external_read']['value'],r['alu']['y']) for r in records],
                         [(1,49,49),(49,255,255),(255,0,0)])
        self.assertEqual(result['rom_reads']['selected_by_alu'],3)
        self.assertEqual(result['rom_reads']['address_counts'],{1:1,49:1,255:1})
        self.assertEqual(result['final_state']['previous_y'],0)
        mapping['fields']['i']['bits']=2|(1<<6)
        unused=execute(mapping,scenario,3,mode='integrated')
        self.assertEqual(unused['rom_reads']['selected_by_alu'],0)
        with self.assertRaisesRegex(ValueError,'integrated mode'):execute(mapping,scenario,1)
        scenario['io']['read']['expected_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):execute(mapping,scenario,1,mode='integrated')
        scenario['io']['read']['address']['bank']=1
        with self.assertRaisesRegex(ValueError,'bank/initial'):validate_scenario(scenario)

    def test_operand_provenance_includes_unchanged_writes(self):
        from operand_study import provenance
        rows=[dict(i=3<<6,a=0,b=10),dict(i=1<<6,a=0,b=11),
              dict(i=3<<6,a=10,b=12)]
        records=[dict(cycle=0,pc=0,registers={},q=0,dispatch_entry=None,next_pc=1),
                 dict(cycle=1,pc=1,registers={},q=0,dispatch_entry=0,next_pc=2),
                 dict(cycle=2,pc=2,registers={'12':7},q=0,dispatch_entry=0,next_pc=3)]
        samples=provenance(records,rows,self.scenario,[1,2])
        self.assertEqual(samples[0]['writers'][0]['pc'],0)
        self.assertEqual(samples[0]['writers'][0]['value'],0)
        self.assertEqual(samples[0]['writers'][1]['kind'],'initial')
        self.assertEqual(samples[0]['writers'][2]['kind'],'initial')
        self.assertEqual(samples[1]['writers'][2]['pc'],2)
        self.assertEqual(samples[1]['source_bytes'],[0,0,7,0])
        with self.assertRaisesRegex(ValueError,'contiguous'):
            provenance(records[1:],rows,self.scenario,[1,2])

    def test_operand_paths_keep_return_context(self):
        from operand_paths import ancestors
        # The same routine at PC 10 is invoked with distinct return addresses.
        edges=[((0,()),(10,(1,))),((10,(1,)),(1,())),
               ((2,()),(10,(3,))),((10,(3,)),(3,()))]
        reached=ancestors(edges,{3})
        self.assertIn((2,()),reached)
        self.assertIn((10,(3,)),reached)
        self.assertNotIn((10,(1,)),reached)
        self.assertNotIn((0,()),reached)
        plain=graph(decode(self.mapping),self.scenario)
        expanded=graph(decode(self.mapping),self.scenario,include_states=True)
        edges=expanded.pop('state_edges')
        self.assertEqual(expanded,plain)
        self.assertEqual({s[0] for edge in edges for s in edge},set(plain['reached']))

    def test_preparation_source_alternative_and_register_role_tradeoff(self):
        from preparation_study import preparation
        from independent_study import arithmetic
        from rotation_study import make_mapping, scenario_for
        config=read(HERE/'preparation-search.json')
        independent=read(HERE/'independent-search.json');base=read(HERE/'rotation-search.json')
        candidate=dict(i=['17.5','!17.3','11.6']+independent['function_bits']+base['destination_bits'])
        mapping=make_mapping(candidate,1,base)
        probe=preparation(decode(mapping),scenario_for(mapping,base)['inputs']['carry'],config['fixture'])
        self.assertEqual([r['source'] for r in probe['trace']],[6]*4)
        self.assertEqual(probe['written_registers'],[0])
        self.assertEqual(probe['final_ram'][10:14],config['fixture']['ram'][10:14])
        self.assertFalse(arithmetic(mapping,independent,base)['failures'])
        swapped=copy.deepcopy(mapping)
        swapped['fields']['a'],swapped['fields']['b']=swapped['fields']['b'],swapped['fields']['a']
        probe=preparation(decode(swapped),scenario_for(swapped,base)['inputs']['carry'],config['fixture'])
        self.assertEqual(probe['written_registers'],[10,11,12,13])
        self.assertTrue(arithmetic(swapped,independent,base)['failures'])

    def test_caller_chain_matches_runner_and_exposes_lost_input(self):
        from chain_study import run_chain
        from rotation_study import scenario_for
        config=read(HERE/'chain-search.json')
        mapping=read(HERE/'results/preparation-study/preparation-source-07.json')
        scenario=scenario_for(mapping,read(HERE/'rotation-search.json'))
        entries={str(site):0 for site in config['dispatch_sites']}
        local=run_chain(decode(mapping),scenario,config,entries,[0]*4,0)
        self.assertEqual(local['cycles'],42)
        self.assertEqual(local['maximum_stack'],3)
        scenario['initial'].update(pc=config['start'],ram=[0]*16,q=0)
        scenario['condition'].update(mode='constant',value=0,polarity=[0]*8)
        scenario['dispatch'].update(mode='constant',value=0)
        scenario['io']['read'].update(mode='constant',value=0)
        result=execute(mapping,scenario,42,mode='integrated')
        self.assertTrue(result['clean'])
        self.assertEqual(result['final_state']['pc'],config['stop'])
        self.assertEqual(result['final_state']['ram'],local['stages']['13E']['ram'])
        self.assertEqual(result['final_state']['q'],local['stages']['13E']['q'])
        swapped=copy.deepcopy(mapping)
        swapped['fields']['a'],swapped['fields']['b']=swapped['fields']['b'],swapped['fields']['a']
        zero=run_chain(decode(swapped),scenario,config,entries,[0]*4,0)
        marked=run_chain(decode(swapped),scenario,config,entries,config['example_data'],0)
        self.assertNotEqual(zero['stages']['134']['ram'],marked['stages']['134']['ram'])
        self.assertEqual(zero['stages']['13E'],marked['stages']['13E'])

    def test_single_caller_preserves_input_in_distinct_candidate_states(self):
        from chain_study import run_chain
        from rotation_study import scenario_for
        config=read(HERE/'single-caller-search.json');fixture=copy.deepcopy(config['fixture'])
        fixture['condition_overrides'].update({str(pc):0 for pc in config['condition_sites']})
        entries={str(config['dispatch_site']):0}
        mapping=read(HERE/'results/preparation-study/preparation-source-07.json')
        mapping['fields']['a'],mapping['fields']['b']=mapping['fields']['b'],mapping['fields']['a']
        scenario=scenario_for(mapping,read(HERE/'rotation-search.json'))
        zero=run_chain(decode(mapping),scenario,fixture,entries,[0]*4,0)
        marked=run_chain(decode(mapping),scenario,fixture,entries,config['example_data'],0)
        self.assertEqual(zero['cycles'],55)
        self.assertNotEqual(zero['stages']['195']['ram'][10],marked['stages']['195']['ram'][10])
        scenario['initial'].update(pc=fixture['start'],ram=[0]*16,q=0)
        scenario['condition'].update(mode='constant',value=0,polarity=[0]*8)
        scenario['dispatch'].update(mode='constant',value=0)
        scenario['io']['read'].update(mode='constant',value=0)
        result=execute(mapping,scenario,55,mode='integrated')
        self.assertTrue(result['clean'])
        self.assertEqual(result['final_state']['pc'],fixture['stop'])
        self.assertEqual(result['final_state']['ram'],zero['stages']['195']['ram'])
        self.assertEqual(result['final_state']['q'],zero['stages']['195']['q'])
        mapping=read(HERE/'results/preparation-study/preparation-source-31.json')
        scenario=scenario_for(mapping,read(HERE/'rotation-search.json'))
        fixture['condition_overrides'].update({str(pc):1 for pc in config['condition_sites']})
        zero=run_chain(decode(mapping),scenario,fixture,entries,[0]*4,0)
        marked=run_chain(decode(mapping),scenario,fixture,entries,config['example_data'],0)
        self.assertNotEqual(zero['stages']['195']['q'],marked['stages']['195']['q'])
        self.assertNotEqual(zero['stages']['195']['ram'][2],marked['stages']['195']['ram'][2])

    def test_first_access_stops_at_replacement_and_reads_before_writes(self):
        from first_use_study import accesses, first_access
        rows=[dict(i=7|(1<<6),a=0,b=0),dict(i=7,a=0,b=0),
              dict(i=2,a=0,b=0),dict(i=2|(1<<6),a=0,b=0)]
        edges=[((0,()),(1,())),((0,()),(2,())),((1,()),(3,())),((2,()),(3,()))]
        result=first_access(rows,edges,(0,()),'Q')
        self.assertEqual([r['pc'] for r in result['reads']],[2])
        self.assertEqual([r['pc'] for r in result['overwrites']],[1])
        self.assertEqual(accesses(dict(i=7|(2<<6),a=10,b=12)),({'R10'},{'R12'}))
        self.assertEqual(accesses(dict(i=7|(4<<6),a=10,b=12)),({'Q'},{'Q','R12'}))
        # A write with an unchanged numerical value still ends the old value's path.
        self.assertNotIn(3,[r['pc'] for r in result['reads']])

    def test_condition_fit_does_not_accept_unknown_flags(self):
        from condition_fit import fit
        observations=[dict(test=1,current=dict(carry=None,zero=1)),dict(test=1,current=dict(carry=0,zero=0))]
        options=fit(observations,'current',['carry','zero'])
        self.assertFalse(any(o['fits'] for o in options))
        carry=next(o for o in options if o['source']=='carry' and o['polarity']==1)
        self.assertEqual((carry['unknown'],carry['mismatches']),(1,0))
        self.assertTrue(fit([dict(test=0,current=dict(zero=1))],'current',['zero'])[1]['fits'])

    def test_pc_keyed_external_read_fixture(self):
        import json
        mapping=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,i=7|(1<<6),a=0,b=0,d=0).items():
            mapping['fields'][name]=dict(bits=bits,status='stub',evidence='PC read fixture')
        scenario=copy.deepcopy(self.scenario)
        scenario['io']['read'].update(mode='pc_table',value=56,pc_values={'0':12,'2':34},status='stub',evidence='fixture')
        with tempfile.TemporaryDirectory() as out:
            result=execute(mapping,scenario,3,mode='integrated',out=out,trace_limit=3)
            records=[json.loads(line) for line in (Path(out)/'trace.jsonl').read_text().splitlines()]
        self.assertTrue(result['clean'])
        self.assertEqual([r['alu']['y'] for r in records],[12,56,34])
        self.assertTrue(all(r['external_read']['source']=='scenario_pc' for r in records))
        scenario['io']['read']['pc_values']['1024']=1
        with self.assertRaisesRegex(ValueError,'PC-keyed'):validate_scenario(scenario)
        scenario['io']['read']['pc_values']={}
        del scenario['io']['read']['evidence']
        with self.assertRaisesRegex(ValueError,'provenance'):validate_scenario(scenario)

    def test_pc_sequence_independent_visits_and_hold(self):
        import json
        mapping=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,i=7|(1<<6),a=0,b=0,d=0).items():
            mapping['fields'][name]=dict(bits=bits,status='stub',evidence='sequence fixture')
        rows=decode(mapping)
        rows[2].update(command=6,branch=0,select=0,direct=1)
        scenario=copy.deepcopy(self.scenario)
        scenario['io']['read'].update(mode='pc_sequence',value=56,
            pc_sequences={'0':[12,34],'2':[78,90,123]},sequence_end='hold-last',
            status='stub',evidence='Independent per-PC visit sequences')
        with tempfile.TemporaryDirectory() as out, patch('execute.decode',return_value=rows):
            result=execute(mapping,scenario,9,mode='integrated',out=out,trace_limit=9)
            records=[json.loads(line) for line in (Path(out)/'trace.jsonl').read_text().splitlines()]
        self.assertTrue(result['clean'])
        self.assertEqual([r['alu']['y'] for r in records],[12,56,78,34,56,90,34,56,123])
        self.assertEqual(result['read_sequence_visits'],{0:3,2:3})
        self.assertTrue(records[6]['external_read']['held_last'])
        self.assertFalse(records[8]['external_read']['held_last'])
        self.assertIsNone(records[1]['external_read']['visit'])
        self.assertEqual(records[6]['external_read']['sequence_index'],1)
        for bad in ({'0':[]},{'00':[1]},{'1024':[1]},{'0':[256]},{'0':[True]}):
            broken=copy.deepcopy(scenario);broken['io']['read']['pc_sequences']=bad
            with self.assertRaisesRegex(ValueError,'PC-keyed'):validate_scenario(broken)
        del scenario['io']['read']['evidence']
        with self.assertRaisesRegex(ValueError,'provenance'):validate_scenario(scenario)

    def test_poll_external_byte_comparison_all_pairs(self):
        from model import Am2901
        mapping=read(HERE/'results/defined-condition-fit/reset-original_previous-zero/mapping.json')
        row=decode(mapping)[0x1ec]
        for register in range(256):
            for data in range(256):
                cpu=Am2901(logic_flags=True);cpu.ram[4]=register
                flags=cpu.step(row['i'],row['a'],row['b'],data,0)
                self.assertEqual(flags['zero'],int(data==(-register)%256))
                self.assertEqual(cpu.ram[4],register)
                self.assertEqual(cpu.ram[3],(data+register)%256)
                self.assertEqual(flags['y'],register)

    def test_poll_caller_provenance_counts_unchanged_writes(self):
        from poll_caller_study import inspect
        rows=[dict(i=64,b=0) for _ in range(1024)]
        rows[0x18d]=dict(i=192,b=3)
        rows[0x19c]=dict(i=192,b=4)
        trace=[dict(pc=pc,cycle=cycle,registers=changes,q=0,carry_in=0,
                    external_read=dict(value=0),alu=dict(f=0))
               for cycle,(pc,changes) in enumerate([(0x18d,{}),(0x19c,{'4':255}),(0x1ec,{})])]
        events=inspect(trace,rows,[0]*16)
        self.assertEqual(events[1]['r3_writer'],dict(pc=0x18d,cycle=0))
        self.assertEqual(events[2]['r4_writer'],dict(pc=0x19c,cycle=1))
        self.assertEqual(events[2]['r4_before'],255)

    def test_drain_trace_rejects_truncation_and_preserves_initial_q(self):
        from double_drain_study import drains
        trace=[dict(pc=0x2d2,q=2),dict(pc=0x1e9,q=1),dict(pc=0x1ea,q=1),
               dict(pc=0x1e9,q=0),dict(pc=0x1ea,q=0),dict(pc=0x1e9,q=0),
               dict(pc=0x1ea,q=0),dict(pc=0x1eb,q=0)]
        self.assertEqual(drains(trace),[dict(initial_q=2,shifted_q=[1,0,0])])
        with self.assertRaisesRegex(ValueError,'unfinished'):drains(trace[:-1])
        with self.assertRaisesRegex(ValueError,'without observed'):drains([trace[-1]])

    def test_context_branch_replacement_is_scoped(self):
        from context_branch_study import alternative
        from common import load
        rows=decode(self.mapping)
        changed=alternative(rows,load(),6,6,0,'!11.0')
        sites=[]
        for before,after in zip(rows,changed):
            selected=before['command']==6 and before['select']==6 and before['direct']
            self.assertEqual(after['branch'],before['branch']^(1 if selected else 0))
            if selected:sites.append(before['pc'])
            self.assertEqual({k:v for k,v in before.items() if k!='branch'},
                             {k:v for k,v in after.items() if k!='branch'})
        self.assertEqual(len(sites),5)
        self.assertEqual(rows,decode(self.mapping))

    def test_joint_branch_deduplication_and_class_separation(self):
        from joint_branch_study import alternatives, combine
        candidate=dict(command=6,select=2,position=0,token='10.0',exceptions=[],
                       changed=[dict(pc=1,before=3,after=2)])
        duplicate=dict(candidate,token='10.1')
        second=dict(candidate,select=3,changed=[dict(pc=2,before=5,after=4)])
        failed=dict(candidate,exceptions=['underflow'])
        choices=alternatives(dict(candidates=[candidate,duplicate,second,failed]))
        self.assertEqual(len(choices),2)
        self.assertEqual(len(choices[0]['sources']),2)
        rows=[dict(pc=i,branch=2*i+1) for i in range(3)]
        original=copy.deepcopy(rows)
        result=combine(rows,*choices)
        self.assertEqual([r['branch'] for r in result],[1,2,4])
        self.assertEqual(rows,original)
        same_class=copy.deepcopy(choices[1]);same_class['sources'][0]['select']=2
        self.assertIsNone(combine(rows,choices[0],same_class))

    def test_branch_mux_gate_polarity_and_direct_scope(self):
        from branch_mux_study import mux
        rows=[dict(pc=i,command=c,direct=d,branch=0x100)
              for i,(c,d) in enumerate([(4,1),(6,1),(6,0),(1,1)])]
        lanes={'17':bytes([0,16,16,16]),'11':bytes([0,4,4,4])}
        original=copy.deepcopy(rows)
        positive=mux(rows,lanes,0,'17.4','11.2')
        negative=mux(rows,lanes,9,'!17.4','!11.2')
        self.assertEqual([r['branch'] for r in positive],[0x100,0x101,0x100,0x100])
        self.assertEqual([r['branch'] for r in negative],[0x300,0x100,0x100,0x100])
        self.assertEqual(rows,original)

    def test_unknown_decision_audit_excludes_unused_test_values(self):
        from condition_extension import unknown_decisions
        scenario=copy.deepcopy(self.scenario)
        scenario['condition'].update(mode='flags',flag_timing='previous',sources=['carry']*8)
        rows=[dict(command=1,select=3,direct=0),dict(command=0,select=3,direct=0),
              dict(command=6,select=0,direct=1),dict(command=3,select=3,direct=0)]
        records=[dict(pc=pc,alu=dict(zero=1,sign=0,carry=None,overflow=None)) for pc in range(4)]
        self.assertEqual(unknown_decisions(records,rows,scenario),{1:1})
        scenario['condition']['flag_timing']='current'
        with self.assertRaisesRegex(ValueError,'previous-flag'):unknown_decisions(records,rows,scenario)

    def test_selector_completion_preserves_fitted_sources(self):
        from selector_completion import complete
        fit=read(HERE/'condition-fit.json')['replay_policies']['original']
        scenario=read(HERE/'results/condition-fit/original-marked/scenario.json')
        before=copy.deepcopy(scenario)
        completed,free=complete(scenario,fit,4)
        self.assertEqual(free,[1,4,5,6])
        self.assertEqual(scenario,before)
        self.assertEqual(completed['condition']['sources'][5],'constant')
        self.assertEqual(completed['condition']['polarity'][5],1)
        for select in map(int,fit):
            self.assertEqual(completed['condition']['sources'][select],scenario['condition']['sources'][select])
            self.assertEqual(completed['condition']['polarity'][select],scenario['condition']['polarity'][select])
        with self.assertRaisesRegex(ValueError,'mask'):complete(scenario,fit,16)

    def test_rom_tail_nested_call_exposes_stack_constraint(self):
        from rom_tail_study import variants
        from rom_study import load_rom
        config=read(HERE/'rom-tail-search.json')
        scenarios=variants(read(HERE/'results/rom-study/scenario-rom_calls.json'),load_rom(config),config)
        rows=decode(self.mapping)
        self.assertEqual(scenarios['outer_tail']['dispatch']['tables']['543']['targets'][-2:],[0x2b3,0x2bc])
        rejected=graph(rows,scenarios['outer_tail'])
        self.assertIn('223: possible stack overflow',rejected['exceptions'])
        nested=graph(rows,scenarios['both_tail'])
        self.assertIn('2c4: possible stack overflow',nested['exceptions'])
        scoped=graph(rows,scenarios['scoped_tail'])
        self.assertFalse(scoped['exceptions'])
        self.assertTrue(set(range(0x2bc,0x2c6))<=set(scoped['reached']))
        self.assertNotIn(0x221,scenarios['scoped_tail']['dispatch']['tables']['708']['targets'])
        self.assertEqual(set(scenarios['scoped_tail']['dispatch']['tables']['708']['targets']),
                         set(scenarios['scoped_byte']['dispatch']['tables']['708']['targets']))

    def test_branch_bit_failure_witness_replays_on_sequencer(self):
        from branch_bit_study import replacement, failure_path
        from common import unconditional_transfer
        from model import X8X02
        scenario=read(HERE/'results/third-case-study/scenario-all_cases.json')
        for position,token,terminal,command in ((0,'!11.0',0x107,2),(9,'!18.7',0x119,3)):
            rows=decode(replacement(self.mapping,position,token))
            path=failure_path(rows,scenario)
            seq=X8X02()
            for source,target in zip(path,path[1:]):
                self.assertEqual(seq.pc,source['pc'])
                self.assertEqual(seq.pushes-seq.pops,len(source['stack']))
                row=rows[seq.pc]
                # These witnesses use direct transfers only, so the chip model
                # can replay them without a dispatch or stack-value stub.
                if row['command'] in (4,6):self.assertTrue(row['direct'])
                choices=[]
                for test in ([True] if unconditional_transfer(row,scenario) else [False,True]):
                    trial=copy.deepcopy(seq)
                    trial.step(row['command'],row['branch'],test)
                    if trial.pc==target['pc'] and trial.pushes-trial.pops==len(target['stack']):choices.append(trial)
                self.assertTrue(choices)
                seq=choices[0]
            self.assertEqual(seq.pc,terminal)
            self.assertEqual(seq.pushes-seq.pops,0)
            self.assertEqual(rows[terminal]['command'],command)

    def test_disconnected_tail_adjustment_preserves_internal_state(self):
        from fragment_study import tail
        for variant in range(1,5):
            rows=decode(read(HERE/f'results/independent-study/variant-{variant}.json'))
            policy=read(HERE/f'results/independent-study/scenario-{variant}.json')['inputs']['carry']
            for a,b in ((0,0),(85,0),(255,255)):
                ram=list(range(16));ram[0]=a;ram[12]=b
                low=tail(rows,policy,0x2d9,ram,165,255,1)
                high=tail(rows,policy,0x2dc,ram,165,255,1)
                minuend=0 if variant==2 else a
                self.assertEqual(low['y'][0],(b-minuend-1)&255)
                self.assertEqual(high['y'][0],(b-minuend)&255)
                self.assertEqual(low['y'][1:],high['y'][1:])
                self.assertTrue(low['state_preserved'] and high['state_preserved'])
                self.assertNotEqual(low['states'][0]['datapath']['flags'],high['states'][0]['datapath']['flags'])
                self.assertEqual(low['states'][1]['datapath'],high['states'][1]['datapath'])
                self.assertEqual(low['states'][2],high['states'][2])
                self.assertEqual(low['states'][2]['pc'],0x07b)

    def test_reset_witness_rejects_actual_failed_run(self):
        from reset_witness_catalog import verify_witness
        config=read(HERE/'reset-witnesses.json')
        entry=copy.deepcopy(config['witnesses'][0])
        entry['path']='results/last-entry-study/q3-extended-00'
        with self.assertRaisesRegex(ValueError,'clean integrated'):
            verify_witness(entry,config['profiles'])

    def test_reset_witness_rejects_truncation_and_tampering(self):
        import json
        import shutil
        from reset_witness_catalog import ARTIFACTS, verify_witness
        config=read(HERE/'reset-witnesses.json');entry=copy.deepcopy(config['witnesses'][0])
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            for name in ARTIFACTS:shutil.copyfile(HERE/entry['path']/name,directory/name)
            entry['path']=temporary
            original=(directory/'trace.jsonl').read_text();lines=original.splitlines(keepends=True)
            (directory/'trace.jsonl').write_text(''.join(lines[:-1]))
            with self.assertRaisesRegex(ValueError,'incomplete witness trace'):
                verify_witness(entry,config['profiles'])
            record=json.loads(lines[0]);record['q']^=1
            (directory/'trace.jsonl').write_text(json.dumps(record,sort_keys=True)+'\n'+''.join(lines[1:]))
            with self.assertRaisesRegex(ValueError,'replay mismatch: trace.jsonl'):
                verify_witness(entry,config['profiles'])
            (directory/'trace.jsonl').write_text(original)
            entry['profile']='q2'
            with self.assertRaisesRegex(ValueError,'named profile'):
                verify_witness(entry,config['profiles'])

    def test_reset_witness_catalog_requires_complete_gap_coverage(self):
        from reset_witness_catalog import build_catalog
        from common import save
        config=read(HERE/'reset-witnesses.json');config['witnesses']=config['witnesses'][:-1]
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'missing.json';save(path,config)
            with self.assertRaisesRegex(ValueError,'missing reset witnesses: 2CF'):
                build_catalog(path)

    def test_program_listing_preserves_profile_scope_and_unresolved_entries(self):
        from program_reading import build, annotations_by_pc
        config=read(HERE/'program-reading.json')
        listing,catalog=build(config)
        self.assertEqual(len(listing),1024)
        self.assertEqual(sum(r['used'] for r in listing),1021)
        self.assertEqual(catalog['counts']['static_reachable'],999)
        self.assertEqual(catalog['counts']['sequencer_sweep_visited'],941)
        self.assertEqual(catalog['counts']['reset_hypothesis_witnesses'],5)
        self.assertEqual(catalog['counts']['default_gaps_with_reset_witness'],22)
        witnesses=catalog['reset_hypothesis_catalog']['witnesses']
        self.assertEqual({w['profile'] for w in witnesses},{'q2','q3','fitted_swapped'})
        self.assertTrue(next(w['conservative_graph_exceptions'] for w in witnesses if w['id']=='q3-masked-ff'))
        import json
        for pc in catalog['unresolved']:
            row=listing[int(pc,16)]
            self.assertEqual(row['explanation_status'],'unresolved entry')
            self.assertFalse(row['static_reachable'])
            self.assertTrue(json.loads(row['reset_hypothesis_witnesses']))
        self.assertEqual(json.loads(listing[0x84]['reset_hypothesis_witnesses']),[])

        self.assertEqual(catalog['counts']['reset_examples'],dict(original=187,swapped=186,q2_nested=187))
        self.assertTrue(listing[0x2bc]['reset_q2_nested_visited'])
        self.assertTrue(listing[0x2ff]['reset_q2_nested_visited'])
        self.assertFalse(listing[0x1df]['reset_q2_nested_visited'])
        self.assertIn('input accumulation',listing[0x002]['q1_labels'])
        self.assertNotIn('input accumulation',listing[0x002]['q2_labels'])
        self.assertIn('equality poll',listing[0x1ec]['fitted_original_labels'])
        self.assertNotIn('equality poll',listing[0x1ec]['fitted_swapped_labels'])
        self.assertIn('quarter-turn',listing[0x3c5]['q2_labels'])
        self.assertNotIn('quarter-turn',listing[0x3c5]['fitted_swapped_labels'])
        self.assertIn('source-overlapping',listing[0x3ef]['q2_labels'])
        self.assertEqual(listing[0x2d9]['explanation_status'],'unresolved entry')
        self.assertIn('transient',listing[0x2d9]['q2_labels'])
        self.assertFalse(listing[0x2d9]['static_reachable'])
        self.assertEqual(listing[0x1df]['explanation_status'],'unused all-FF word')
        invalid=copy.deepcopy(config);invalid['annotations'][0]['profiles']=['missing-layout']
        with self.assertRaisesRegex(ValueError,'profile scope'):annotations_by_pc(invalid)
        invalid=copy.deepcopy(config);invalid['annotations'][0]['ranges']=[['3FE','400']]
        with self.assertRaisesRegex(ValueError,'outside control store'):annotations_by_pc(invalid)

    def test_logical_flags_are_explicit_and_remove_unknown_feedback(self):
        m=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,select=3,i=7|(3<<3)|(1<<6),a=0,b=0,d=0,carry=0,carry_select=1).items():
            m['fields'][name]=dict(bits=bits,status='stub',evidence='OR zero fixture')
        s=copy.deepcopy(self.scenario)
        s['inputs']['carry']=dict(mode='mapped-or-previous',initial=0,unknown=0,
            constant_field='carry',select_field='carry_select',status='stub',evidence='fixture')
        old=execute(m,s,2,mode='integrated')
        self.assertEqual(old['carry_model']['counts']['unknown_feedback'],1)
        s['inputs']['logic_flags']=dict(mode='am2901b-ripple',status='hypothesis',evidence='AMD Figure 9; ripple connection')
        new=execute(m,s,2,mode='integrated')
        self.assertEqual(new['carry_model']['previous'],1)
        self.assertNotIn('unknown_feedback',new['carry_model']['counts'])
        with self.assertRaisesRegex(ValueError,'logical flag model requires integrated mode'):execute(m,s,2)
        del s['inputs']['logic_flags']['evidence']
        with self.assertRaisesRegex(ValueError,'logic flags'):execute(m,s,2,mode='integrated')
        s['inputs']['logic_flags']=None
        with self.assertRaisesRegex(ValueError,'logic flags'):execute(m,s,2,mode='integrated')

    def test_split_slice_instruction_links_reach_execution(self):
        m=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,select=3,i=7|(3<<3),a=0,b=0,d=0xA5).items():
            m['fields'][name]=dict(bits=bits,status='stub',evidence='split-slice fixture')
        s=copy.deepcopy(self.scenario)
        s['initial']['q']=0xC0
        s['inputs']['logic_flags']=dict(mode='am2901b-ripple',status='hypothesis',evidence='AMD Figure 9')
        s['inputs']['slice_instruction']=dict(
            high_from_low={'6':2},status='hypothesis',
            evidence='facing-pin candidate fixture',
            undriven_shift=dict(value=0,status='stub',evidence='diagnostic floating input'))
        with tempfile.TemporaryDirectory() as temporary:
            result=execute(m,s,1,mode='integrated',out=temporary,trace_limit=1)
            row=json.loads((Path(temporary)/'trace.jsonl').read_text().splitlines()[0])
        self.assertEqual(result['final_state']['q'],0xC5)
        self.assertEqual((row['instruction_i'],row['instruction_i_high']),
                         (7|(3<<3),(7|(3<<3))|(1<<6)))
        invalid=copy.deepcopy(s)
        invalid['inputs']['slice_instruction']['high_from_low']={'6':9}
        with self.assertRaisesRegex(ValueError,'split-slice instruction links'):
            execute(m,invalid,1,mode='integrated')
        invalid=copy.deepcopy(s)
        del invalid['inputs']['slice_instruction']['undriven_shift']
        with self.assertRaisesRegex(ValueError,'undriven shift level'):
            execute(m,invalid,1,mode='integrated')

    def test_split_slice_high_address_override_is_independent(self):
        m=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,select=3,i=0x87,a=0,b=2,d=0).items():
            m['fields'][name]=dict(bits=bits,status='stub',evidence='high A fixture')
        s=copy.deepcopy(self.scenario)
        s['initial']['ram'][0]=0xAB
        s['initial']['ram'][1]=0xF0
        s['inputs']['logic_flags']=dict(mode='am2901b-ripple',status='hypothesis',evidence='ripple fixture')
        s['inputs']['slice_instruction']=dict(
            high_from_low={'4':4},status='hypothesis',evidence='identity link fixture',
            undriven_shift=dict(value=0,status='stub',evidence='unused shift fixture'))
        policy=lambda value:dict(value=value,status='hypothesis',evidence='independent high A test')
        s['inputs']['register_address_bit_overrides']={'a_high':{'0':policy(0)}}
        s['inputs']['register_address_bit_overrides_by_pc']={'0':{'a_high':{'0':policy(1)}}}
        with tempfile.TemporaryDirectory() as temporary:
            execute(m,s,2,mode='integrated',out=temporary,trace_limit=2)
            rows=[json.loads(line) for line in (Path(temporary)/'trace.jsonl').read_text().splitlines()]
        self.assertEqual([row['register_address_a_high'] for row in rows],[1,0])
        self.assertEqual([row['alu']['y'] for row in rows],[0xFB,0xAB])
        invalid=copy.deepcopy(s)
        del invalid['inputs']['slice_instruction']
        with self.assertRaisesRegex(ValueError,'register address overrides'):
            validate_scenario(invalid)

    def test_previous_flags_start_unknown(self):
        m=copy.deepcopy(self.mapping)
        for name,bits in dict(command=1,select=3,i=7|(1<<6),a=0,b=0,d=0).items():
            m['fields'][name]=dict(bits=bits,status='stub',evidence='fixture')
        self.scenario['condition'].update(mode='flags',flag_timing='previous',unknown=1)
        result=execute(m,self.scenario,2,mode='integrated')
        self.assertEqual(result['assumption_counts']['unknown carry'],1)

    def test_stack_aware_dispatch_graph(self):
        rows=[dict(pc=p,command=1,branch=0,direct=1,select=0,unused=False) for p in range(1024)]
        # Computed call -> two POP entries -> return to self-loop at 1.
        rows[0].update(command=4,direct=0)
        rows[1].update(command=6,branch=1)
        rows[10]['command']=rows[14]['command']=3
        s=copy.deepcopy(self.scenario)
        s['dispatch']['tables']['0']=dict(base=10,count=2,stride=4,status='hypothesis')
        g=graph(rows,s)
        self.assertIn((0,10,'dispatch:hypothesis'),g['edges'])
        self.assertIn((0,14,'dispatch:hypothesis'),g['edges'])
        self.assertIn((14,1,'return'),g['edges'])
        self.assertEqual(set(g['reached']),{0,1,10,14})

    def test_sequence_dispatch_and_am27s31(self):
        m=copy.deepcopy(self.mapping)
        for name,bits in dict(command=4,direct=0,select=1).items():
            m['fields'][name]=dict(bits=bits,status='stub',evidence='fixture')
        # A constant command needs a dispatch rule for every address.
        self.scenario['dispatch']['tables']={str(p):dict(base=100,count=4,stride=4,status='stub',evidence='fixture') for p in range(1024)}
        self.scenario['condition'].update(mode='constant',value=1)
        self.scenario['dispatch'].update(mode='sequence',sequence=[2])
        a=execute(m,self.scenario,1)
        self.assertEqual(a['final_state']['pc'],108)
        self.scenario['io']['read']['mode']='am27s31'
        a=execute(m,self.scenario,1)
        self.assertEqual(len(a['am27s31_hash']),64)

if __name__=='__main__': unittest.main()
