"""Score all 137 diagnostic ROM gates against q3 cyclic D-consuming words."""
import argparse
from collections import Counter
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
    catalog=read(ASSUMED/'program-reading.json')
    mapping_path=ASSUMED/catalog['profiles']['q3']
    scenario_path=ASSUMED/catalog['scenario']
    gate_path=ASSUMED/'results/rom-gate-study/report.json'
    rows=decode(read(mapping_path))
    flow=graph(rows,read(scenario_path),include_states=True)
    assert not flow['exceptions']
    cyclic_pcs={state[0] for component in cyclic_components(flow['state_edges'])
                for state in component}
    fits=read(gate_path)['fits']
    assert len(fits)==137
    hit_counts=Counter();empty=0;paired=0;fit_summaries=[]
    for fit in fits:
        selected=set(fit['d_selected_pcs'])
        cyclic=sorted(selected&cyclic_pcs)
        output_loop=sorted(selected&set(range(0x38c,0x3a2)))
        if not cyclic:empty+=1
        if output_loop:paired+=1
        hit_counts.update(cyclic)
        fit_summaries.append(dict(id=fit['id'],terms=fit['terms'],
                                  cyclic_d_pcs=[f'{pc:03X}' for pc in cyclic],
                                  paired_output_d_pcs=[f'{pc:03X}' for pc in output_loop]))
    assert empty==73 and paired==0
    retained={pc for pc in hit_counts if (rows[pc]['i']>>6)&7 not in (1,)}
    assert retained=={0x1ec,0x36c,0x36e}
    return dict(status='family-wide diagnostic gate/cycle screen',
        gate_fit_count=len(fits),fits_without_cyclic_d=empty,
        fits_with_d_in_paired_output_loop=paired,
        cyclic_d_site_counts={f'{pc:03X}':count for pc,count in sorted(hit_counts.items())},
        cyclic_d_sites_with_register_write=[f'{pc:03X}' for pc in sorted(retained)],
        fits=fit_summaries,
        source_sha256={str(path.relative_to(ASSUMED)):hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (mapping_path,scenario_path,gate_path)},
        interpretation='None of the 137 diagnostic gate fits selects a D operand in q3 paired-output loop 38C–3A1. Seventy-three select no D-consuming word in any declared cyclic component. Cyclic D-driven register writes occur only at 1EC, 36C and 36E among the remaining fits.',
        limitations=['All 137 gates were fitted to assumed diagnostic labels, not physical ROM read-enable measurements.',
                     'The q3 graph follows one declared stack/dispatch policy and overapproximates conditional branch feasibility.',
                     'A ROM value could be captured before a loop, or an untested gate/mapping could select other words.',
                     'This screen does not identify a transmitter or prove the actual board lacks one.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/all-rom-gate-cycles.json')
    args=parser.parse_args();result=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['gate_fit_count'],result['fits_without_cyclic_d'],
          result['fits_with_d_in_paired_output_loop'],result['cyclic_d_site_counts'])


if __name__=='__main__':main()
