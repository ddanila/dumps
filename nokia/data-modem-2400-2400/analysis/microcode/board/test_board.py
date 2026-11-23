import json
import tempfile
import unittest
from pathlib import Path
from engine import Engine, Stop, validate
from logic import Word, resolve, mux
from run_board import run
from decode import inspect, successors
from validate_evidence import audit


def cell(typ, **inputs): return {'type':typ, 'inputs':inputs}


def board(cells, external=None):
    return {'name':'synthetic fixture','status':'synthetic-test','components':cells,
            'external':{k:{'width':v} for k,v in (external or {}).items()}}


def rom(data, **inputs):
    c=cell('PROM',**inputs); c['rom']={'bytes':data}; return c


class LogicTests(unittest.TestCase):
    def test_unknown_and_tristate(self):
        self.assertEqual((Word.x(4)&Word.of(0,4)).integer(),0)
        self.assertEqual((Word.x(4)|Word.of(15,4)).integer(),15)
        self.assertEqual(Word.z(4).integer(),None)
        self.assertEqual(resolve([Word.z(4),Word.of(7,4)]).integer(),7)
        with self.assertRaisesRegex(ValueError,'contention'): resolve([Word.of(0,1),Word.of(1,1)])
        self.assertEqual(mux(Word.of(3,4),Word.of(3,4),Word.x(1)).integer(),3)
        self.assertEqual(mux(Word.of(3,4),Word.of(7,4),Word.x(1)).text(),'0X11')

    def test_nibble_arithmetic_flags_exhaustive(self):
        signed=lambda n:n if n<8 else n-16
        for a in range(16):
            for b in range(16):
                for c in (0,1):
                    f,carry,ovr=Word.of(a,4).add(Word.of(b,4),Word.of(c,1))
                    self.assertEqual(f.integer(),(a+b+c)&15)
                    self.assertEqual(carry.integer(),int(a+b+c>=16))
                    self.assertEqual(ovr.integer(),int(not -8<=signed(a)+signed(b)+c<=7))


class NetworkTests(unittest.TestCase):
    def test_validation(self):
        b=board({'R':cell('REG374',D=['EXT.data[0]']*8,CLK='EXT.clk',OEn=0)}, {'data':8,'clk':1})
        self.assertFalse(validate(b)['errors'])
        b['components']['R']['inputs']['D']='EXT.data[8]'
        self.assertTrue(validate(b)['errors'])
        b['components']['R']['inputs']['D']='R.CLK'
        self.assertTrue(validate(b)['errors'])
        b['components']['R']['type']='UNSUPPORTED'
        self.assertTrue(validate(b)['errors'])

    def test_latch_and_register_timing(self):
        b=board({'R':cell('REG374',D='EXT.d',CLK='EXT.c',OEn='EXT.oe'),
                 'L':cell('LATCH373',D='EXT.d',LE='EXT.c',OEn='EXT.oe')},{'d':8,'c':1,'oe':1})
        e=Engine(b);e.initialize({'d':17,'c':0,'oe':0})
        self.assertIsNone(e.values['R.Q'].integer())
        e.step({'c':1});self.assertEqual(e.values['R.Q'].integer(),17)
        e.step({'d':34});self.assertEqual(e.values['R.Q'].integer(),17)
        self.assertEqual(e.values['L.Q'].integer(),34)
        e.step({'c':0});e.step({'d':51})
        self.assertEqual(e.values['L.Q'].integer(),34)
        e.step({'oe':1});e.step({'c':1})
        self.assertEqual(e.values['R.Q'].text(),'ZZZZZZZZ')
        e.step({'oe':0});self.assertEqual(e.values['R.Q'].integer(),51)

    def test_simultaneous_registers_sample_old_state(self):
        b=board({'A':cell('REG374',D='EXT.d',CLK='EXT.c',OEn=0),
                 'B':cell('REG374',D='A.Q',CLK='EXT.c',OEn=0)}, {'d':8,'c':1})
        e=Engine(b);e.initialize({'d':42,'c':0});e.step({'c':1})
        self.assertIsNone(e.values['B.Q'].integer())
        e.step({'c':0});e.step({'c':1})
        self.assertEqual(e.values['B.Q'].integer(),42)

    def test_prom_address_and_data_permutation(self):
        b=board({'P':rom([i&255 for i in range(1024)],A=['EXT.a[1]','EXT.a[0]']+[f'EXT.a[{i}]' for i in range(2,10)],ENn=0),
                 'R':cell('REG374',D=[f'P.D[{i}]' for i in reversed(range(8))],CLK='EXT.c',OEn=0)}, {'a':10,'c':1})
        e=Engine(b);e.initialize({'a':1,'c':0})
        self.assertEqual(e.values['P.D'].integer(),2)
        e.step({'c':1});self.assertEqual(e.values['R.Q'].integer(),64)

    def test_rom_hash_and_size_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.bin';path.write_bytes(bytes(1024))
            b=board({'P':cell('PROM',A=0,ENn=0)})
            b['components']['P']['rom']={'path':'bad.bin','sha256':'0'*64}
            with self.assertRaisesRegex(ValueError,'hash mismatch'):Engine(b,Path(tmp))
        b=board({'P':rom([0],A=0,ENn=0)})
        with self.assertRaisesRegex(ValueError,'1024 bytes'):Engine(b)

    def test_mux_disabled_and_unknown_select(self):
        b=board({'M':cell('MUX157',A=1,B=3,S=None,ENn=0)})
        e=Engine(b);e.initialize({});self.assertEqual(e.values['M.Y'].text(),'00X1')
        b['components']['M']['inputs']['ENn']=1
        e=Engine(b);e.initialize({});self.assertEqual(e.values['M.Y'].integer(),0)

    def test_unknown_and_uninitialized_stack_stop(self):
        for cmd, message in [(None,'AC'),(3,'next address')]:
            b=board({'S':cell('SEQ8X02',AC=cmd,B=0,TEST=0,CLK='EXT.c',ENn=0)},{'c':1})
            e=Engine(b);e.initialize({'c':1})
            with self.assertRaisesRegex(Stop,message):e.step({'c':0})

    def test_static_decode_and_conditional_edges(self):
        here=Path(__file__).resolve().parent
        b=json.loads((here/'synthetic-demo.json').read_text())
        e=Engine(b)
        row=inspect(e,0)
        self.assertEqual(row['lanes']['P']['physical_address'],0)
        self.assertEqual(row['fields']['AC'],4)
        self.assertEqual(row['edges'],[{'target':4,'condition':'TEST=1'}])
        self.assertEqual({x['target'] for x in successors(1023,0)}, {0,1})
        self.assertIsNone(successors(0,3)[0]['target'])
        self.assertIsNone(inspect(Engine(json.loads((here/'dsc2847.json').read_text()),here),0)['fields']['AC'])

    def test_saved_synthetic_demo_and_evidence_audit(self):
        here=Path(__file__).resolve().parent
        self.assertFalse(audit(here)['errors'])
        with tempfile.TemporaryDirectory() as tmp:
            result=run(here/'synthetic-demo.json',here/'synthetic-scenario.json',Path(tmp),8)
            self.assertEqual(result['completed_cycles'],8)
            self.assertEqual(result['events'],32)
            self.assertEqual(result['stop'],'cycle limit')
            rows=[json.loads(x) for x in (Path(tmp)/'trace.jsonl').read_text().splitlines()]
            addresses=[int(x['signals']['S.A'],2) for x in rows if 'execute rise' in x['phase']]
            self.assertEqual(addresses,[4,1,2,3,0,4,1,2])

    def test_unknown_clock_transition(self):
        e=Engine(board({'R':cell('REG374',D=0,CLK='EXT.c',OEn=0)},{'c':1}))
        e.initialize({})
        with self.assertRaisesRegex(Stop,'ambiguous transition'):e.step({'c':1})

    def test_real_board_stops_without_guessing_clock(self):
        here=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            a=run(here/'dsc2847.json',here/'startup.json',Path(tmp)/'a',3)
            b=run(here/'dsc2847.json',here/'startup.json',Path(tmp)/'b',3)
            self.assertEqual(a,b);self.assertEqual(a['completed_cycles'],0)
            self.assertIn('clock schedule',a['stop'])
            self.assertEqual((Path(tmp)/'a/trace.jsonl').read_bytes(),(Path(tmp)/'b/trace.jsonl').read_bytes())


class SequencerTests(unittest.TestCase):
    def machine(self):
        return Engine(board({'S':cell('SEQ8X02',AC='EXT.ac',B='EXT.b',TEST='EXT.t',CLK='EXT.c',ENn=0)},
                            {'ac':3,'b':10,'t':1,'c':1}))

    def cycle(self,e,ac,b=0,t=0):
        e.step({'ac':ac,'b':b,'t':t});e.step({'c':0});e.step({'c':1})
        return e.values['S.A'].integer()

    def test_calls_skips_loops_and_reset(self):
        e=self.machine();e.initialize({'ac':1,'b':0,'t':0,'c':1})
        self.assertEqual(self.cycle(e,4,100,1),100)
        self.assertEqual(self.cycle(e,0,t=1),102)
        self.assertEqual(self.cycle(e,3),1)
        self.assertEqual(self.cycle(e,5),2)
        self.assertEqual(self.cycle(e,2,t=0),3)
        self.assertEqual(e.state['S']['sp'],0)
        self.assertEqual(self.cycle(e,6,9,1),9)
        self.assertEqual(self.cycle(e,7),0)

    def test_changed_phase_controls_rejected(self):
        e=self.machine();e.initialize({'ac':1,'b':0,'t':0,'c':1})
        e.step({'c':0});e.step({'ac':7})
        with self.assertRaisesRegex(Stop,'controls changed'):e.step({'c':1})

    def test_synthetic_control_store_pipeline(self):
        data=[1]*1024;data[0]=4;data[4]=3  # call 4, return to 1
        b=board({'S':cell('SEQ8X02',AC=['R.Q[0]','R.Q[1]','R.Q[2]'],B=4,TEST=1,CLK='EXT.sc',ENn=0),
                 'P':rom(data,A='S.A',ENn=0),
                 'R':cell('REG374',D='P.D',CLK='EXT.rc',OEn=0)}, {'sc':1,'rc':1})
        e=Engine(b);e.initialize({'sc':1,'rc':0})
        for expected in [4,1,2]:
            e.step({'rc':1});e.step({'rc':0});e.step({'sc':0});e.step({'sc':1})
            self.assertEqual(e.values['S.A'].integer(),expected)


class SliceTests(unittest.TestCase):
    def test_two_slices_write_ram_and_carry(self):
        inputs=dict(I='EXT.i',A=0,B=0,D='EXT.dlo',Cn=0,CLK='EXT.c',OEn=0,
                    RAM0in=0,RAM3in='H.RAM0out',Q0in=0,Q3in='H.Q0out')
        hi={**inputs,'D':'EXT.dhi','Cn':'L.Cn4','RAM0in':'L.RAM3out','RAM3in':0,'Q0in':'L.Q3out','Q3in':0}
        e=Engine(board({'L':cell('AM2901',**inputs),'H':cell('AM2901',**hi)},
                       {'i':9,'dlo':4,'dhi':4,'c':1}))
        # DZ OR RAMF initializes register 0 to 0x7f without reading unknown RAM.
        e.initialize({'i':7+(3<<3)+(3<<6),'dlo':15,'dhi':7,'c':1})
        e.step({'c':0});e.step({'c':1})
        self.assertEqual(e.state['L']['ram'][0].integer(),15)
        self.assertEqual(e.state['H']['ram'][0].integer(),7)
        # DA ADD RAMF: 0x7f + 1 = 0x80, carry between real separate slice objects.
        e.step({'i':5+(3<<6),'dlo':1,'dhi':0})
        self.assertEqual(e.values['L.F'].integer(),0)
        self.assertEqual(e.values['H.F'].integer(),8)
        self.assertEqual(e.values['H.OVR'].integer(),1)
        e.step({'c':0});e.step({'c':1})
        self.assertEqual(e.state['H']['ram'][0].integer(),8)
        # Load 0x91, then divide by two: bit 4 must cross into the low slice.
        e.step({'i':7+(3<<3)+(3<<6),'dlo':1,'dhi':9})
        e.step({'c':0});e.step({'c':1})
        e.step({'i':4+(3<<3)+(5<<6)})
        e.step({'c':0});e.step({'c':1})
        self.assertEqual(e.state['H']['ram'][0].integer(),4)
        self.assertEqual(e.state['L']['ram'][0].integer(),8)
        # Q shifts also cross the slice boundary and sample the old Q values.
        e.step({'i':7+(3<<3),'dlo':1,'dhi':9})
        e.step({'c':0});e.step({'c':1})
        self.assertEqual((e.state['H']['q'].integer()<<4)|e.state['L']['q'].integer(),0x91)
        e.step({'i':4+(3<<3)+(4<<6)})
        e.step({'c':0});e.step({'c':1})
        self.assertEqual((e.state['H']['q'].integer()<<4)|e.state['L']['q'].integer(),0x48)
        e.step({'i':4+(3<<3)+(6<<6)})
        e.step({'c':0});e.step({'c':1})
        self.assertEqual((e.state['H']['q'].integer()<<4)|e.state['L']['q'].integer(),0x90)

    def test_unknown_initial_data_is_preserved(self):
        inputs=dict(I=0,A=0,B=0,D=0,Cn=0,CLK='EXT.c',OEn=0,RAM0in=0,RAM3in=0,Q0in=0,Q3in=0)
        e=Engine(board({'A':cell('AM2901',**inputs)},{'c':1}));e.initialize({'c':0})
        e.step({'c':1})
        self.assertIsNone(e.state['A']['q'].integer())


if __name__=='__main__':unittest.main()
