"""Check direct destination bytes after the masked q3 nested reset path."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, read, save, decode
from register_contract_study import capture, resume, verify_full


def scenario_for(base, config, payload, first, second):
    scenario = copy.deepcopy(base)
    scenario.update(name='q3 masked nested load and direct destination bytes', evidence=config['evidence'])
    scenario['io']['read']['evidence'] = config['evidence']
    scenario['io']['read']['pc_sequences'].update({str(0x225):[payload], str(0x089):[first,second]})
    for pc in (0x07e,0x081):
        scenario['dispatch']['tables'][str(pc)].update(index_source='previous_y', evidence=config['evidence'])
    return scenario


def prediction(snapshot, payload, d, first, second):
    ram = snapshot['ram'][:]
    value = payload >> 1
    helper5 = ((d-payload-1)&255) >> 1
    # q3 28E/28F add D+Q; 293 replaces R15 with Q-D, then 295 adds one.
    ram[3] = (d+payload)&255
    ram[15] = (payload-d+1)&255
    # 07C and 07E both write D+Q to R2, before either indexed store.
    ram[2] = (d+payload)&255
    ram[0],ram[5] = value,helper5
    ram[first] = value
    ram[0],ram[5] = value,helper5
    ram[second] = value
    return dict(ram=ram, q=payload, value=value, helper5=helper5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/q3-register-contract')
    args = parser.parse_args()
    config = read(HERE/'q3-register-contract.json')
    base_path = HERE/config['base']
    mapping,base = read(base_path/'mapping.json'),read(base_path/'scenario.json')
    rows = decode(mapping)
    snapshot = capture(mapping,base,config,args.out/'prefix')
    counts = Counter(); digest = hashlib.sha256(); witnesses = []
    for payload in range(256):
        for first in range(16):
            for second in range(16):
                scenario = scenario_for(base,config,payload,first,second)
                got = resume(rows,scenario,snapshot,payload,first,second,read_values=[first,second])
                want = prediction(snapshot,payload,base['io']['read']['value'],first,second)
                assert got['ram'] == want['ram'] and got['q'] == payload
                assert got['cycles'] == 42 and got['max_depth'] == 4
                assert [t['index'] for t in got['dispatches']] == [first,second]
                assert [t['register'] for t in got['dispatches']] == [first,second]
                lost = got['ram'][first] != want['value']
                assert lost == (first == 5 and second != 5)
                counts['contract_cases'] += 1
                counts['first_value_absent_at_finish'] += int(lost)
                counts['first_r6_second_address_unchanged'] += int(first == 6)
                digest.update(json.dumps([payload,first,second,got],sort_keys=True,separators=(',',':')).encode())
                if [payload,first,second] in config['witnesses']:
                    out = args.out/f'q{payload:02x}-r{first:02d}-r{second:02d}'
                    trace_digest = verify_full(mapping,scenario,config,snapshot,got,out)
                    witnesses.append(dict(path=out.name,payload=payload,first=first,second=second,
                        prediction=want,dispatches=got['dispatches'],trace_digest=trace_digest))
        if payload%64 == 63:
            print(payload+1,'payloads',dict(counts),flush=True)
    sources = [Path(__file__),HERE/'q3-register-contract.json',HERE/'register_contract_study.py',
        HERE/'affine_tail_study.py',HERE/'common.py',HERE/'execute.py',HERE/'defined_condition_fit.py',
        HERE.parent/'model.py',*(base_path/name for name in ('mapping.json','scenario.json','trace.jsonl','summary.json'))]
    save(args.out/'report.json',dict(configuration=config,snapshot=snapshot,counts=dict(counts),
        execution_sha256=digest.hexdigest(),witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 diagnostic contract: each 089 external byte directly selects the register through previous Y. Payload Q is retained and Q>>1 is stored twice. First R5 is overwritten by the second helper; first R6 does not change the second address. Real zero-reset prefix and four-frame stack; selected complete core runs match every continuation step. Physical read/index wiring and controller protocol remain hypotheses.'))


if __name__ == '__main__':
    main()
