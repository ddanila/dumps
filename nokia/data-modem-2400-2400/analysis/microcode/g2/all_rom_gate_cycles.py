"""Score all 137 diagnostic ROM gates against cyclic words in six mappings."""
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


def selected_d_pcs(rows, activated_pcs):
    """Operand selection belongs to the current mapping, not the gate fit."""
    return {pc for pc in activated_pcs
            if rows[pc].get('i') is not None and rows[pc]['i'] & 7 in (5, 6, 7)}


def cyclic_write_counts(rows, fits, cyclic_pcs):
    counts = Counter()
    for fit in fits:
        for pc in selected_d_pcs(rows, fit['pcs']) & cyclic_pcs:
            # Every destination except NOP writes RAM and/or Q, including shifts.
            if (rows[pc]['i'] >> 6) & 7 != 1:
                counts[pc] += 1
    return {f'{pc:03X}': count for pc, count in sorted(counts.items())}


def run():
    catalog=read(ASSUMED/'program-reading.json')
    mapping_paths={name:ASSUMED/rel for name,rel in catalog['profiles'].items()}
    mapping_path=mapping_paths['q3']
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
        selected=selected_d_pcs(rows, fit['pcs'])
        cyclic=sorted(selected&cyclic_pcs)
        output_loop=sorted(selected&set(range(0x38c,0x3a2)))
        if not cyclic:empty+=1
        if output_loop:paired+=1
        hit_counts.update(cyclic)
        fit_summaries.append(dict(id=fit['id'],terms=fit['terms'],
                                  cyclic_d_pcs=[f'{pc:03X}' for pc in cyclic],
                                  paired_output_d_pcs=[f'{pc:03X}' for pc in output_loop]))
    assert empty==73 and paired==0
    by_mapping={}
    for name,path in mapping_paths.items():
        mapped=decode(read(path))
        mapped_flow=graph(mapped,read(scenario_path),include_states=True)
        assert not mapped_flow['exceptions']
        mapped_cyclic={state[0] for component in cyclic_components(mapped_flow['state_edges'])
                       for state in component}
        counts=cyclic_write_counts(mapped, fits, mapped_cyclic)
        by_mapping[name]=dict(cyclic_d_register_writes=counts,
                              operations=[dict(pc=pc, operation=mapped[int(pc,16)]['operation'],
                                               a=mapped[int(pc,16)]['a'], b=mapped[int(pc,16)]['b'])
                                          for pc in counts],
                              cyclic_pc_count=len(mapped_cyclic))
    retained={int(pc,16) for pc in by_mapping['q3']['cyclic_d_register_writes']}
    return dict(status='family-wide diagnostic gate/cycle screen',
        gate_fit_count=len(fits),fits_without_cyclic_d=empty,
        fits_with_d_in_paired_output_loop=paired,
        cyclic_d_site_counts={f'{pc:03X}':count for pc,count in sorted(hit_counts.items())},
        cyclic_d_sites_with_register_write=[f'{pc:03X}' for pc in sorted(retained)],
        by_mapping=by_mapping,
        fits=fit_summaries,
        source_sha256={str(path.relative_to(ASSUMED)):hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (*mapping_paths.values(),scenario_path,gate_path)},
        interpretation='Operand selection is recomputed separately for each mapping from the gate activation PCs. q3/q4 retain three cyclic D-write sites; q1/q2 additionally admit 05E, 061, 127 and 12C; the fitted mappings additionally admit 187, 299, 29B and 29C. The top-level fit summaries describe q3 only.',
        correction='The previous report incorrectly reused d_selected_pcs cached under q3 when screening the other five mappings. Its claim that every mapping had the same three sites is withdrawn.',
        limitations=['All 137 gates were fitted to assumed diagnostic labels, not physical ROM read-enable measurements.',
                     'The graph follows one declared stack/dispatch policy and overapproximates conditional branch feasibility.',
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
