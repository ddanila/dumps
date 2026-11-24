"""Shared, provenance-preserving decode for the assumption-driven experiment."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from run import load, field_value

NAMES = ['TSK', 'INC', 'BLT', 'POP', 'BSR', 'PLP', 'BRT', 'RST']
STATUS = {'recovered-from-data', 'hypothesis', 'stub'}
WIDTHS = dict(command=3, branch=10, select=3, direct=1, i=9, i_high=9,
              a=4, b=4, d=8,
              carry=1, carry_select=1, ram_in=1, q_in=1)


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def validate(mapping):
    for name in ('command', 'branch', 'select', 'direct'):
        if name not in mapping['fields']:
            raise ValueError(f'missing field {name}')
    for name, field in mapping['fields'].items():
        if field['status'] not in STATUS or not field.get('evidence'):
            raise ValueError(f'{name}: missing provenance')
        bits = field['bits']
        width = WIDTHS.get(name, 4)
        if isinstance(bits, int):
            if not 0 <= bits < 1 << width:
                raise ValueError(f'{name}: constant out of range')
        else:
            if len(bits) != width:
                raise ValueError(f'{name}: width mismatch')
            for token in bits:
                chip, bit = token.lstrip('!').split('.')
                if chip not in ('10', '11', '17', '18') or not 0 <= int(bit) < 8:
                    raise ValueError(f'{name}: invalid bit {token}')
        contexts = field.get('commands', list(range(8)))
        if not all(c in range(8) for c in contexts):
            raise ValueError('invalid command context')


def decode(mapping, lanes=None):
    validate(mapping)
    lanes = load() if lanes is None else lanes
    rows = []
    for pc in range(1024):
        command = field_value(mapping['fields']['command']['bits'], lanes, pc)
        row = {k: field_value(v['bits'], lanes, pc) for k, v in mapping['fields'].items()
               if command in v.get('commands', range(8))}
        row.update(pc=pc, raw=[lanes[c][pc] for c in ('10', '11', '17', '18')])
        used_bits={t.lstrip('!') for v in mapping['fields'].values()
                   if command in v.get('commands',range(8)) and isinstance(v['bits'],list) for t in v['bits']}
        row['remaining_raw']={c:lanes[c][pc] & sum(1<<b for b in range(8) if f'{c}.{b}' not in used_bits) for c in lanes}
        row['command_name']=NAMES[command]
        if 'i' in row:
            sources=['A,Q','A,B','0,Q','0,B','0,A','D,A','D,Q','D,0']
            functions=['R+S+C','~R+S+C','R+~S+C','R|S','R&S','~R&S','R^S','~(R^S)']
            destinations=['Q=F','no load','RAM[B]=F; Y=A','RAM[B]=F','RAM[B]=F>>1; Q>>1','RAM[B]=F>>1','RAM[B]=F<<1; Q<<1','RAM[B]=F<<1']
            i=row['i']
            row['operation']=f'R,S={sources[i&7]}; F={functions[(i>>3)&7]}; {destinations[(i>>6)&7]}'
        row['unused'] = row['raw'] == [255] * 4
        rows.append(row)
    return rows


def unconditional_transfer(row, scenario):
    condition = scenario['condition']
    eligible = (row['command'] in (4, 6)
            and row['select'] == condition['unconditional_select']
            and (row['direct'] or not condition.get('unconditional_requires_direct', True)))
    gate = condition.get('brt_unconditional_gate')
    if not eligible or row['command'] != 6 or gate is None:
        return eligible
    def value(token):
        chip, bit = token.lstrip('!').split('.')
        raw = row['raw'][('10','11','17','18').index(chip)]
        return bool(((raw >> int(bit)) & 1) ^ token.startswith('!'))
    return all(any(value(token) for token in clause) for clause in gate['clauses'])


def validate_brt_gate(gate):
    """Validate a provenance-owned conjunction of raw-bit OR clauses."""
    tokens = {f'{inv}{chip}.{bit}' for inv in ('','!')
              for chip in ('10','11','17','18') for bit in range(8)}
    if (not isinstance(gate,dict) or gate.get('status') not in STATUS
            or not gate.get('evidence')):
        raise ValueError('BRT unconditional gate requires provenance')
    clauses = gate.get('clauses')
    if (not isinstance(clauses,list) or not clauses
            or any(not isinstance(c,list) or not c
                   or any(not isinstance(t,str) or t not in tokens for t in c)
                   for c in clauses)):
        raise ValueError('BRT unconditional gate requires nonempty raw-bit clauses')


def table_targets(table):
    """Resolve a regular table or an explicit, provenance-owned sparse target list."""
    if 'targets' in table:
        if any(k in table for k in ('base','count','stride')):
            raise ValueError('ambiguous dispatch table format')
        targets=table['targets']
        if not isinstance(targets,list) or not targets:
            raise ValueError('empty or invalid dispatch targets')
    else:
        base,count,stride=(table.get(k) for k in ('base','count','stride'))
        if any(type(v) is not int for v in (base,count,stride)) or not 1<=count<=1024 or stride<1:
            raise ValueError('invalid dispatch table bounds')
        targets=[base+i*stride for i in range(count)]
    allow_duplicates=table.get('allow_duplicate_targets',False)
    if type(allow_duplicates) is not bool:raise ValueError('invalid duplicate-target policy')
    if any(type(p) is not int or not 0<=p<1024 for p in targets) or (not allow_duplicates and len(set(targets))!=len(targets)):
        raise ValueError('invalid or duplicate dispatch targets')
    return targets
