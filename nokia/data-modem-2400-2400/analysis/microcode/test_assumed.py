"""Behavioral checks for the assumption-driven workflow."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'assumed'))
from common import HERE, decode, field_value, read, validate
from analyze import graph, must_targets, search_address, walk, rank_layouts
from execute import CarryInput, execute, validate_scenario
from register_study import recover_register, table_semantics


class AssumedTests(unittest.TestCase):
    def setUp(self):
        self.mapping=read(HERE/'sequencer.json')
        self.scenario=read(HERE/'baseline.json')

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
