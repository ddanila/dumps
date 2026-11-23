"""Evidence-aware functional event model; no implicit Nokia wiring or clocks."""
from copy import deepcopy
from pathlib import Path
import hashlib
import re
from logic import Word, mux, resolve


class Stop(RuntimeError):
    pass


# Formal signal ports, not physical pin numbers. Inventory maps known pins.
PORTS = {
    'PROM': ({'A': 10, 'ENn': 1}, {'D': 8}),
    'REG374': ({'D': 8, 'CLK': 1, 'OEn': 1}, {'Q': 8}),
    'LATCH373': ({'D': 8, 'LE': 1, 'OEn': 1}, {'Q': 8}),
    'SEQ8X02': ({'AC': 3, 'B': 10, 'TEST': 1, 'CLK': 1, 'ENn': 1}, {'A': 10}),
    'AM2901': ({'I': 9, 'A': 4, 'B': 4, 'D': 4, 'Cn': 1, 'CLK': 1, 'OEn': 1,
                'RAM0in': 1, 'RAM3in': 1, 'Q0in': 1, 'Q3in': 1},
               {'Y': 4, 'F': 4, 'Cn4': 1, 'OVR': 1, 'ZERO': 1, 'SIGN': 1,
                'RAM0out': 1, 'RAM3out': 1, 'Q0out': 1, 'Q3out': 1}),
    'MUX157': ({'A': 4, 'B': 4, 'S': 1, 'ENn': 1}, {'Y': 4}),
    'BUFFER': ({'D': 8, 'ENn': 1}, {'Y': 8}),
    'AND': ({'A': 1, 'B': 1}, {'Y': 1}),
    'OR': ({'A': 1, 'B': 1}, {'Y': 1}),
    'XOR': ({'A': 1, 'B': 1}, {'Y': 1}),
    'NOT': ({'A': 1}, {'Y': 1}),
    'COUNTER4': ({'D': 4, 'CLK': 1, 'LOADn': 1, 'ENn': 1, 'UP': 1}, {'Q': 4}),
}
DECODE_FIELDS = {'AC':3, 'BRANCH':10, 'TEST':1, 'I_LOW':9, 'I_HIGH':9, 'A_LOW':4, 'B_LOW':4, 'A_HIGH':4, 'B_HIGH':4}
REFERENCE = re.compile(r'([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)(?:\[(\d+)\])?$')


def need(value, context):
    n = value.integer()
    if n is None: raise Stop(f'{context}: unresolved {value.text()}')
    return n


def validate(board):
    errors, missing = [], []
    cells = board.get('components', {})
    external = board.get('external', {})
    def width(expr):
        if expr is None or isinstance(expr, int): return None
        if isinstance(expr, list):
            for item in expr:
                n = width(item)
                if n not in (None, 1): raise ValueError('bit list contains a non-scalar reference')
                if isinstance(item, int) and item not in (0, 1): raise ValueError('invalid bit constant')
            return len(expr)
        if isinstance(expr, dict):
            if set(expr) == {'not'}: return width(expr['not'])
            if set(expr) == {'bus'} and expr['bus']:
                sizes = {width(x) for x in expr['bus']} - {None}
                if len(sizes) > 1: raise ValueError('bus width mismatch')
                return next(iter(sizes), None)
            raise ValueError('invalid expression')
        match = REFERENCE.fullmatch(expr)
        if not match: raise ValueError(f'invalid endpoint {expr}')
        cell, port, bit = match.groups()
        if cell == 'EXT': n = external[port]['width']
        else: n = PORTS[cells[cell]['type']][1][port]
        if bit is not None:
            if not 0 <= int(bit) < n: raise ValueError(f'bit out of range: {expr}')
            return 1
        return n
    for cell, spec in cells.items():
        typ = spec.get('type')
        if typ not in PORTS:
            errors.append(f'{cell}: unsupported component {typ}'); continue
        inputs = spec.get('inputs', {})
        for extra in inputs.keys() - PORTS[typ][0].keys(): errors.append(f'{cell}.{extra}: invalid input port')
        for port, n in PORTS[typ][0].items():
            expr = inputs.get(port)
            if expr is None: missing.append(f'{cell}.{port}')
            try:
                actual = width(expr)
                if actual not in (None, n): raise ValueError(f'expected width {n}, got {actual}')
                if isinstance(expr, int): Word.of(expr, n)
            except (ValueError, KeyError, TypeError) as err: errors.append(f'{cell}.{port}: {err}')
    for name, expr in board.get('decode', {}).items():
        try:
            if name not in DECODE_FIELDS: raise ValueError('unknown decode field')
            actual = width(expr)
            if actual not in (None, DECODE_FIELDS[name]): raise ValueError('decode width mismatch')
            if isinstance(expr, int): Word.of(expr, DECODE_FIELDS[name])
        except (ValueError, KeyError, TypeError) as err: errors.append(f'decode {name}: {err}')
    for name, expr in board.get('observables', {}).items():
        try: width(expr)
        except (ValueError, KeyError, TypeError) as err: errors.append(f'observable {name}: {err}')
    return {'errors': errors, 'unconnected_inputs': missing,
            'unresolved_evidence': board.get('unresolved', [])}


class Engine:
    def __init__(self, board, base=Path('.')):
        self.board = board
        report = validate(board)
        if report['errors']: raise ValueError('; '.join(report['errors']))
        self.cells = board['components']
        self.ext = {k: Word.x(v['width']) for k, v in board.get('external', {}).items()}
        self.state, self.roms, self.values = {}, {}, {}
        self.event = 0
        for name, cell in self.cells.items():
            typ = cell['type']
            if typ == 'PROM':
                desc = cell['rom']
                if 'bytes' in desc:
                    if board.get('status') != 'synthetic-test': raise ValueError('inline ROM allowed only for synthetic-test boards')
                    data = bytes(desc['bytes'])
                else:
                    data = (base / desc['path']).resolve().read_bytes()
                    if hashlib.sha256(data).hexdigest() != desc['sha256']: raise ValueError(f'{name}: ROM hash mismatch')
                if len(data) != 1024: raise ValueError(f'{name}: ROM must have 1024 bytes')
                self.roms[name] = data
            elif typ in ('REG374', 'LATCH373'): self.state[name] = {'q': Word.x(8)}
            elif typ == 'COUNTER4': self.state[name] = {'q': Word.x(4)}
            elif typ == 'SEQ8X02':
                self.state[name] = {'pc': Word.of(0, 10), 'sp': 0, 'stack': [Word.x(10)]*4, 'pending': None, 'sample': None}
            elif typ == 'AM2901':
                self.state[name] = {'ram': [Word.x(4)]*16, 'q': Word.x(4), 'a': Word.x(4), 'b': Word.x(4)}
            for port, n in PORTS[typ][1].items(): self.values[f'{name}.{port}'] = Word.x(n)

    def expr(self, expr, width):
        if expr is None: return Word.x(width)
        if isinstance(expr, int): return Word.of(expr, width)
        if isinstance(expr, list): return Word(tuple(self.expr(x, 1).bits[0] for x in expr))
        if isinstance(expr, dict):
            if 'not' in expr: return ~self.expr(expr['not'], width)
            try: return resolve([self.expr(x, width) for x in expr['bus']])
            except ValueError as err: raise Stop(str(err)) from err
        name, port, bit = REFERENCE.fullmatch(expr).groups()
        value = self.ext[port] if name == 'EXT' else self.values[f'{name}.{port}']
        return Word((value.bits[int(bit)],)) if bit is not None else value

    def inputs(self, name):
        cell = self.cells[name]
        return {p: self.expr(cell.get('inputs', {}).get(p), w) for p, w in PORTS[cell['type']][0].items()}

    def alu(self, name, inputs):
        state = self.state[name]
        code = inputs['I'].integer()
        if code is None: return {p: Word.x(n) for p, n in PORTS['AM2901'][1].items()}
        a, b, q, d, zero = state['a'], state['b'], state['q'], inputs['D'], Word.of(0, 4)
        r, s = [(a,q), (a,b), (zero,q), (zero,b), (zero,a), (d,a), (d,q), (d,zero)][code & 7]
        fn, dest = (code >> 3) & 7, code >> 6
        if fn < 3:
            f, carry, overflow = ((~r if fn == 1 else r).add(~s if fn == 2 else s, inputs['Cn']))
        else:
            f = [r | s, r & s, (~r) & s, r ^ s, ~(r ^ s)][fn-3]
            carry = overflow = Word.x(1)  # unimplemented logic-mode flag equations, never zero-filled
        iszero = Word.of(0, 1) if 1 in f.bits else Word.of(1, 1) if f.integer() == 0 else Word.x(1)
        right, left = dest in (4,5), dest in (6,7)
        return {'F': f, 'Y': (a if dest == 2 else f).gate(inputs['OEn']),
                'Cn4': carry, 'OVR': overflow, 'ZERO': iszero, 'SIGN': Word((f.bits[3],)),
                'RAM0out': Word((f.bits[0],)) if right else Word.z(1),
                'RAM3out': Word((f.bits[3],)) if left else Word.z(1),
                'Q0out': Word((q.bits[0],)) if right else Word.z(1),
                'Q3out': Word((q.bits[3],)) if left else Word.z(1)}

    def outputs(self, name, i):
        typ, state = self.cells[name]['type'], self.state.get(name)
        if typ == 'PROM':
            addr = i['A'].integer()
            word = Word.x(8) if addr is None else Word.of(self.roms[name][addr], 8)
            return {'D': word.gate(i['ENn'])}
        if typ in ('REG374', 'LATCH373'): return {'Q': state['q'].gate(i['OEn'])}
        if typ == 'COUNTER4': return {'Q': state['q']}
        if typ == 'SEQ8X02': return {'A': state['pc'].gate(i['ENn'])}
        if typ == 'AM2901': return self.alu(name, i)
        if typ == 'MUX157': return {'Y': mux(mux(i['A'],i['B'],i['S']), Word.of(0,4), i['ENn'])}
        if typ == 'BUFFER': return {'Y': i['D'].gate(i['ENn'])}
        if typ == 'NOT': return {'Y': ~i['A']}
        return {'Y': i['A'].binary(i['B'], typ.lower())}

    def settle(self):
        for _ in range(64):
            new = {}
            for name in self.cells:
                for port, value in self.outputs(name, self.inputs(name)).items(): new[f'{name}.{port}'] = value
            changed = new != self.values
            self.values = new
            # Transparent storage behavior is separate from edge-triggered updates.
            for name, cell in self.cells.items():
                i, state = self.inputs(name), self.state.get(name)
                if cell['type'] == 'LATCH373':
                    q = mux(state['q'], i['D'], i['LE'])
                    changed |= q != state['q']; state['q'] = q
                elif cell['type'] == 'AM2901':
                    clk = i['CLK'].integer()
                    if clk == 1:
                        for port, slot in [('A','a'), ('B','b')]:
                            address = i[port].integer()
                            value = Word.x(4) if address is None else state['ram'][address]
                            changed |= value != state[slot]; state[slot] = value
                    elif clk == 0:
                        code = need(i['I'], f'{name}.I while RAM write phase is active')
                        dest = code >> 6
                        if dest >= 2:
                            b = need(i['B'], f'{name}.B RAM write address')
                            f = self.alu(name,i)['F']
                            if dest in (4,5): f = Word(f.bits[1:]+i['RAM3in'].bits)
                            if dest in (6,7): f = Word(i['RAM0in'].bits+f.bits[:3])
                            changed |= f != state['ram'][b]; state['ram'][b] = f
            if not changed: return
        raise Stop('combinational/transparent-storage network did not settle in 64 iterations')

    def sequencer_fall(self, name, i, state):
        command = need(i['AC'], f'{name}.AC at falling edge')
        pc = need(state['pc'], f'{name} current address')
        test = need(i['TEST'], f'{name}.TEST') if command in (0,2,4,6) else 0
        nxt = Word.of((pc+1) & 1023,10)
        if command == 0: nxt = Word.of((pc+1+test)&1023,10)
        elif command in (2,3):
            if command == 3 or test: nxt = state['stack'][state['sp']]
            state['sp'] = (state['sp']-1)&3
        elif command in (4,5):
            if command == 5 or test:
                state['sp'] = (state['sp']+1)&3
                state['stack'][state['sp']] = Word.of(pc,10) if command == 5 else nxt
                if command == 4: nxt = i['B']
        elif command == 6 and test: nxt = i['B']
        elif command == 7: nxt = Word.of(0,10)
        need(nxt, f'{name} next address')
        state['pending'] = nxt
        # This functional two-phase adapter requires stable relevant controls.
        state['sample'] = {'AC': i['AC']}
        if command in (0,2,4,6): state['sample']['TEST'] = i['TEST']
        if command in (4,6) and test: state['sample']['B'] = i['B']

    def edges(self, before, after):
        updates = deepcopy(self.state)
        for name, cell in self.cells.items():
            typ = cell['type']
            if 'CLK' not in PORTS[typ][0]: continue
            old, new = before[name]['CLK'].integer(), after[name]['CLK'].integer()
            if old == new: continue
            if old is None or new is None: raise Stop(f'{name}.CLK ambiguous transition; establish a known idle level first')
            i, s = before[name], updates[name]  # sample data before the edge
            if typ == 'REG374' and new == 1: s['q'] = i['D']
            elif typ == 'SEQ8X02':
                if new == 0: self.sequencer_fall(name, i, s)
                else:
                    if s['pending'] is None: raise Stop(f'{name}: rising edge without a modeled falling phase')
                    if any(i[k] != v for k,v in s['sample'].items()):
                        raise Stop(f'{name}: controls changed between phases; unsupported sequencer timing')
                    s['pc'], s['pending'], s['sample'] = s['pending'], None, None
            elif typ == 'AM2901':
                code = need(i['I'], f'{name}.I at clock edge')
                if new == 1:
                    dest = code >> 6
                    if dest == 0: s['q'] = self.alu(name,i)['F']
                    elif dest == 4: s['q'] = Word(s['q'].bits[1:]+i['Q3in'].bits)
                    elif dest == 6: s['q'] = Word(i['Q0in'].bits+s['q'].bits[:3])
            elif typ == 'COUNTER4' and new == 1:
                if need(i['LOADn'], f'{name}.LOADn') == 0: s['q'] = i['D']
                elif need(i['ENn'], f'{name}.ENn') == 0:
                    n = s['q'].integer()
                    delta = 1 if need(i['UP'],f'{name}.UP') else -1
                    s['q'] = Word.x(4) if n is None else Word.of((n+delta)&15,4)
        self.state = updates

    def initialize(self, initial):
        for key, value in initial.items():
            if key not in self.ext: raise ValueError(f'unknown external input {key}')
            self.ext[key] = Word.of(value, len(self.ext[key].bits))
        self.settle()

    def step(self, changes):
        # Settle a simultaneous input event, sampling all devices from the
        # same old state. Sequentially generated clocks are rejected below.
        before = {name:self.inputs(name) for name in self.cells}
        for key, value in changes.items():
            if key not in self.ext: raise ValueError(f'unknown external input {key}')
            self.ext[key] = Word.of(value, len(self.ext[key].bits))
        # Compute new combinational values without transparent state updates yet.
        for _ in range(64):
            new = {f'{name}.{p}':v for name in self.cells for p,v in self.outputs(name,self.inputs(name)).items()}
            if new == self.values: break
            self.values = new
        else: raise Stop('combinational event did not settle')
        after = {name:self.inputs(name) for name in self.cells}
        self.edges(before, after)
        self.settle()
        # Generated clocks from sequential outputs require a further event wave;
        # reject them explicitly rather than silently missing an edge.
        settled = {name:self.inputs(name) for name in self.cells}
        for name in self.cells:
            if 'CLK' in after[name] and after[name]['CLK'] != settled[name]['CLK']:
                raise Stop(f'{name}: sequentially generated clock requires a timing adapter')
        self.event += 1

    def snapshot(self):
        def encode(value):
            if isinstance(value, Word): return value.text()
            if isinstance(value, dict): return {k:encode(v) for k,v in value.items()}
            if isinstance(value, list): return [encode(v) for v in value]
            return value
        return {'event':self.event, 'inputs':encode(self.ext), 'signals':encode(self.values), 'state':encode(self.state)}
