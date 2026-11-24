"""Locate cyclic q3 control states that can read the candidate ROM D bus."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ASSUMED=HERE.parent/'assumed'
sys.path.insert(0,str(ASSUMED))
from common import decode, read  # noqa: E402
from analyze import graph  # noqa: E402
from phase_add_screen import cyclic_components  # noqa: E402


def run():
    config=read(ASSUMED/'program-reading.json')
    mapping_path=ASSUMED/config['profiles']['q3']
    scenario_path=ASSUMED/config['scenario']
    gate_path=ASSUMED/'results/rom-gate-study/report.json'
    rows=decode(read(mapping_path))
    flow=graph(rows,read(scenario_path),include_states=True)
    assert not flow['exceptions']
    fits=read(gate_path)['fits']
    gate=next(fit for fit in fits if fit['terms']==[['11.4',0],['18.5',0]])
    selected=set(gate['d_selected_pcs'])
    groups={}
    for component in cyclic_components(flow['state_edges']):
        pcs={state[0] for state in component}
        reads=pcs&selected
        if not reads:continue
        key=tuple(sorted(pcs))
        record=groups.setdefault(key,dict(component_count=0,cyclic_pcs=[f'{pc:03X}' for pc in key],
            rom_d_pcs=[f'{pc:03X}' for pc in sorted(reads)],
            operations=[dict(pc=f'{pc:03X}',operation=rows[pc].get('operation'),
                             a=rows[pc].get('a'),b=rows[pc].get('b')) for pc in key]))
        record['component_count']+=1
    result=list(groups.values())
    assert {tuple(x['cyclic_pcs']) for x in result}=={
        ('02B','02C','02D','02E'),('1EC','1ED'),('36C','36D','36E')}
    return dict(status='candidate ROM-D cyclic screen under q3 declared control graph',
        gate_terms=gate['terms'],gate_status='diagnostic fit, not physical read-enable',
        cyclic_component_count=len(cyclic_components(flow['state_edges'])),
        rom_d_cycle_shapes=result,
        source_sha256={str(path.relative_to(ASSUMED)):hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (mapping_path,scenario_path,gate_path)},
        interpretation='Only three distinct q3 cycle shapes contain a D-selected word under the two-bit gate. 02C does not load state; 1EC–1ED is a two-word poll; 36C–36E is the separately checked ROM-address/carry recurrence. None is a demonstrated transmit phase loop.',
        limitations=['The two-bit gate is fitted to diagnostic labels and is not traced physical wiring.',
                     'The graph includes both branch outcomes but only the declared dispatch targets and stack policy.',
                     'Other gates, mappings, entries or multiword dataflow outside these cycles may implement modulation.',
                     'This is static control-flow analysis, not a new running transmitter.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/rom-cycle-screen.json')
    args=parser.parse_args();result=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print([(x['cyclic_pcs'],x['rom_d_pcs']) for x in result['rom_d_cycle_shapes']])


if __name__=='__main__':main()
