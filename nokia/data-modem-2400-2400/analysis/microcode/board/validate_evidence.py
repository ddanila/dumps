"""Validate physical identifiers without promoting trace fragments to nets."""
import json
from pathlib import Path


def audit(folder):
    inventory=json.loads((folder/'inventory.json').read_text())
    nets=json.loads((folder/'nets.json').read_text())
    board=json.loads((folder/'dsc2847.json').read_text())
    parts={p['ref']:p for p in inventory['parts']}
    errors=[]
    if len(parts)!=len(inventory['parts']): errors.append('duplicate component reference')
    for part in parts.values():
        mapping=inventory['pinmaps'].get(part.get('pinmap'),{})
        for name,pins in mapping.items():
            for pin in pins:
                if not part['package_pins'] or not 1<=pin<=part['package_pins']:
                    errors.append(f'{part["ref"]}.{name}: invalid physical pin {pin}')
    for fragment in nets.get('trace_fragments',[]):
        ref,pin=fragment['endpoint'].split(' ')[0].split('.')
        if ref not in parts or not 1<=int(pin)<=(parts[ref]['package_pins'] or 0):
            errors.append(f'{fragment["id"]}: invalid endpoint')
        if not (folder/fragment['view']).is_file():errors.append(f'{fragment["id"]}: evidence view missing')
    for ref in board['components']:
        if ref not in parts:errors.append(f'{ref}: absent from inventory')
    return {'errors':errors,'positions':len(parts),'runtime_components':len(board['components']),
            'complete_executable_nets':len(nets['executable_nets']),
            'trace_fragments':len(nets.get('trace_fragments',[])),
            'candidate_bundles':len(nets['candidate_bundles']),
            'unresolved_part_identifications':[r for r,p in parts.items() if p['status']=='unresolved'],
            'unmodeled_populated_positions':[r for r,p in parts.items() if r not in board['components'] and r!='U16'],
            'note':'Physical identifier consistency only; this does not validate continuity.'}


if __name__=='__main__':
    report=audit(Path(__file__).resolve().parent)
    print(json.dumps(report,indent=2))
    raise SystemExit(bool(report['errors']))
