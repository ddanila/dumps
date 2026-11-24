"""Test whether q3's known ROM operand path forms a V.26 ter phase loop."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path.insert(0, str(ASSUMED))
from common import read
from defined_condition_fit import load_trace
from execute import execute
from handler_timing_study import classify
from sine_operand_study import scenario_for_phase
from table_signatures import ROM, SHA


def probe(out):
    config = read(ASSUMED/'sine-operand-study.json')
    mapping = read(ASSUMED/config['profiles']['q3'])
    rom = ROM.read_bytes()
    assert hashlib.sha256(rom).hexdigest() == SHA
    cases = []
    for dibit in range(4):
        address = 0x7c + dibit
        scenario = scenario_for_phase(config, 'q3', address)
        policy = scenario['io']['read']
        policy['address']['bank'] = 0
        policy['address']['evidence'] = ('G2 lower-bank test of the existing PC317 previous-Y ROM operand path; '
            'the address originates from the diagnostic D316 input, not from controller USART bits.')
        policy['evidence'] = policy['address']['evidence']
        scenario['name'] = f'G2 q3 lower-bank Gray operand {dibit}'
        result = execute(mapping, scenario, 160, mode='integrated', out=out/f'dibit-{dibit}', trace_limit=160)
        trace = load_trace(out/f'dibit-{dibit}')
        reads = [r for r in trace if 'address' in r.get('external_read',{})]
        outputs = [r for r in trace if r['pc'] == 0x392]
        terminal = [r for r in trace if r['pc'] == 0x84]
        assert result['clean'] and result['unused_word_executions'] == 0
        assert len(reads) == 1 and reads[0]['pc'] == 0x317
        assert reads[0]['cycle'] == 45 and reads[0]['external_read']['address'] == address
        assert reads[0]['external_read']['value'] == rom[address]
        assert reads[0]['external_read']['selected_by_alu']
        assert len(outputs) == 1 and outputs[0]['cycle'] == 55
        assert outputs[0]['alu']['y'] == 2*(5+rom[address])
        assert terminal and terminal[0]['cycle'] == 110
        assert all(r['pc'] == 0x84 for r in trace[110:])
        finding = classify(trace, scenario)
        assert finding['outcome'] == 'terminal'
        cases.append(dict(dibit=['00','01','10','11'][dibit],rom_address=f'{address:03X}',
            rom_byte=rom[address],first_output=outputs[0]['alu']['y'],
            rom_read_cycle=45,output_cycle=55,first_terminal_cycle=110,
            final_q=result['final_state']['q'], final_pc=f'{result["final_state"]["pc"]:03X}',
            trace_digest=result['trace_digest']))
    return dict(status='negative for this q3 scenario, not a global transmitter exclusion',
        cases=cases,rom_sha256=SHA,
        configuration=dict(mapping=config['profiles']['q3'],base=config['scenario'],
            bank=0,read_pc='317',address_source='previous Y',address_input_pc='316',
            code=5,cycles=160),
        interpretation='One diagnostic input selects one real ROM operand and one output; every run reaches terminal 084 at cycle 110. No persistent phase update or repeated sample stream occurs.',
        limitations=['D316 is a diagnostic input, not a traced USART connection.',
            'The ROM bank, enable and output port are unverified hardware choices.',
            'Different control/condition and datapath mappings may have a transmitter path.'],
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),HERE/'table_signatures.py',ASSUMED/'sine_operand_study.py',
                ASSUMED/'paired_components_study.py',ASSUMED/'handler_timing_study.py',
                ASSUMED/'execute.py',ASSUMED/'common.py',ASSUMED.parent/'model.py',
                ASSUMED/'sine-operand-study.json',ASSUMED/config['profiles']['q3'])})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/gray-operand-probe')
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    result = probe(args.out)
    (args.out/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print([(c['dibit'],c['rom_address'],c['rom_byte'],c['first_output'],c['first_terminal_cycle'])
           for c in result['cases']])


if __name__ == '__main__':
    main()
