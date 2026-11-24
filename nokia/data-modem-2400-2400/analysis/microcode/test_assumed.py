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
