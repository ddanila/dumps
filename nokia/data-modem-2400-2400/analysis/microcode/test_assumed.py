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
from execute import execute, validate_scenario


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
