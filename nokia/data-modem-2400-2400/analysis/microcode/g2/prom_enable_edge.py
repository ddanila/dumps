"""Exercise the candidate U10 E2/U5 capture edge with four-state chip models."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / 'board'
sys.path.insert(0, str(BOARD))
from engine import Engine

SOURCE = BOARD / 'dsc2847.json'


def build():
    original = json.loads(SOURCE.read_text())
    # E1/E3/E4 are assumed asserted. The one-bit active-low ENn models E2.
    # U5 D0 is the photo-inferred enable route; D1..D7 are a deliberately
    # generous identity bundle from U10, so this is a best case for retention.
    return dict(name='U10 E2 to U5 capture-edge hypothesis',
                status='photo-informed-hypothesis',
                external={'address': {'width': 10}, 'e2': {'width': 1},
                          'clock': {'width': 1}},
                components={
                    'U10': dict(original['components']['U10'],
                                inputs={'A': 'EXT.address', 'ENn': 'EXT.e2'}),
                    'U5': dict(original['components']['U5'], inputs={
                        'D': ['EXT.e2'] + [f'U10.D[{bit}]' for bit in range(1, 8)],
                        'CLK': 'EXT.clock', 'OEn': 0})})


def capture(sequence):
    engine = Engine(build(), BOARD)
    # Word 004 is EC in the real U10 dump, making retained data visible.
    engine.initialize(dict(address=4, e2=0, clock=0))
    observations = []
    for name, event in sequence:
        engine.step(event)
        observations.append(dict(event=name, prom=engine.values['U10.D'].text(),
                                 latch=engine.values['U5.Q'].text(),
                                 latch_bit0=engine.values['U5.Q'].bits[0]))
    return observations


def run(out):
    cases = {
        'read_then_latch': [('latch edge while E2 low', {'clock': 1})],
        'disable_then_latch': [('E2 high before edge', {'e2': 1}),
                               ('latch edge while E2 high', {'clock': 1})],
        'latch_then_disable': [('latch edge while E2 low', {'clock': 1}),
                               ('E2 high after edge', {'e2': 1})],
        'simultaneous_change': [('E2 and latch clock change in one event',
                                 {'e2': 1, 'clock': 1})],
    }
    observations = {name: capture(events) for name, events in cases.items()}
    assert observations['read_then_latch'][-1]['latch'] == '11101100'
    assert observations['read_then_latch'][-1]['latch_bit0'] == 0
    assert observations['disable_then_latch'][-1]['latch_bit0'] == 1
    assert observations['disable_then_latch'][-1]['latch'][:7] == 'ZZZZZZZ'
    assert observations['latch_then_disable'][-1]['latch_bit0'] == 0
    assert observations['simultaneous_change'][-1]['latch_bit0'] == 0
    report = dict(status='minimal edge-model diagnostic, not complete board timing',
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), SOURCE, BOARD/'engine.py',
                                              BOARD/'logic.py')},
                  assumptions=['Other U10 enables are asserted.',
                               'U5 D1..D7 are generously modeled as direct U10 data bits; their actual permutation is unresolved.',
                               'REG374 samples its D pins on a rising edge; no extra bus hold or second latch is modeled.'],
                  cases=observations,
                  finding='With this simple route, a capture of E2=1 also captures high-impedance U10 data; a valid data capture stores E2=0. A separate holding circuit or different I0 route is required for I0=1 with valid U10 fields.',
                  limitations=['No propagation delays or analog capacitance are represented.',
                               'The E2-to-U5 route and other U10-to-U5 bits are photo candidates, not continuity measurements.',
                               'This does not run the full DSP program or identify its line output.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    result = run(HERE/'results/prom-enable-edge.json')
    print({name: rows[-1]['latch'] for name, rows in result['cases'].items()})
