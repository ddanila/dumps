"""Follow independent captured bytes through q2's paired arithmetic from reset."""
import argparse
import copy
import hashlib
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save
from defined_condition_fit import load_trace
from execute import execute


def scenario_for(base, config, low, high, entry):
    scenario = copy.deepcopy(base)
    scenario['name'] = 'independent captured pair and preceding-Y selector'
    scenario['initial'] = dict(pc=0, ram=[0]*16, q=0)
    scenario['io']['read'] = dict(mode='pc_sequence', value=1, table=[0],
        pc_sequences={str(0x117): [1, 0], str(0x106): [1, 0],
                      str(0x118): [(low+1)&255], str(0x107): [(high+1)&255],
                      str(0x38e): [entry], str(0x36d): [0]},
        sequence_end='hold-last', status='stub', evidence=config['evidence'])
    return scenario


def inspect(trace, low, high, entry):
    """Compare executed byte outputs with independent 16-bit arithmetic."""
    value = low | high << 8
    expected = (2*value)&65535 if entry < 2 else 0
    releases = expected >> 8 == 0
    ram = [0]*16
    first_dispatch = None
    outputs = []
    returns = []
    loop_tests = []
    first_terminal = None
    captures = {}
    start = 0x392 + 4*entry
    for t in trace:
        pc = t['pc']
        if pc in (0x118, 0x107):
            register, byte = (6, low) if pc == 0x118 else (7, high)
            assert t['alu']['f'] == byte
            captures[str(register)] = dict(pc=pc, cycle=t['cycle'],
                input=t['external_read']['value'], value=byte)
        if pc == 0x38f:
            assert ram[4:12] == [0, 0, low, high, 0, 0, low, high]
            assert t['dispatch_input'] == entry and t['dispatch_entry'] == entry
            assert t['next_pc'] == start
            if first_dispatch is None:
                first_dispatch = dict(cycle=t['cycle'], ram=ram[:], q=t['q'])
        if start <= pc < start+4:
            offset = pc-start
            want = (0, 0, expected&255, expected>>8)[offset]
            assert t['alu']['f'] == t['alu']['y'] == want
            assert not t['registers'] and t['q'] == 0
            if len(outputs) < 4:
                outputs.append(dict(pc=pc, cycle=t['cycle'], value=want,
                                    carry=t['alu']['carry'], zero=t['alu']['zero']))
        if pc == 0x390:
            assert t['test'] == int(not releases)
            assert t['next_pc'] == (0x391 if releases else 0x389)
            loop_tests.append(t['cycle'])
        if pc == 0x391:
            assert t['next_pc'] == 0x347
            returns.append(t['cycle'])
        if pc == 0x36d:
            assert t['external_read']['value'] == t['alu']['carry'] == 0
        if pc == 0x84 and first_terminal is None:
            first_terminal = t['cycle']
        for r, byte in t['registers'].items():
            ram[int(r)] = byte
    assert first_dispatch is not None and len(outputs) == 4 and loop_tests
    assert set(captures) == {'6', '7'}
    assert bool(returns) == (first_terminal is not None) == releases
    assert len(returns) == int(releases)
    assert ram[6:8] == ram[10:12] == [low, high]
    if not releases:
        assert len(loop_tests) >= 2
        assert all(b-a == 12 for a, b in zip(loop_tests, loop_tests[1:]))
    return dict(value=value, expected_pair=expected, releases=releases,
        nonzero_low_on_return=releases and expected != 0,
        captures=captures, first_dispatch=first_dispatch, outputs=outputs,
        first_loop_test=loop_tests[0], wrapper_return=returns[0] if returns else None,
        first_terminal=first_terminal, final_captured_pair=ram[10:12])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/paired-capture-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'paired-capture-study.json')
    mapping, base = (read(HERE/config[k]) for k in ('mapping', 'scenario'))
    counts = Counter()
    runs = []
    witnesses = []
    with tempfile.TemporaryDirectory() as temporary:
        for high in config['high_bytes']:
            for low in range(256):
                for entry in range(4):
                    scenario = scenario_for(base, config, low, high, entry)
                    name = f'h{high:02x}-l{low:02x}-e{entry}'
                    keep = [low, high, entry] in config['witnesses']
                    out = args.out/name if keep else Path(temporary)
                    result = execute(mapping, scenario, config['cycles'], mode='integrated',
                                     out=out, trace_limit=config['cycles'])
                    assert result['clean'] and result['unused_word_executions'] == 0
                    observed = inspect(load_trace(out), low, high, entry)
                    outcome = 'terminal' if observed['releases'] else 'paired-loop'
                    assert (result['final_state']['pc'] == 0x84) == observed['releases']
                    counts[f'entry{entry}:{outcome}'] += 1
                    counts['nonzero_low_on_return'] += int(observed['nonzero_low_on_return'])
                    runs.append(dict(low=low, high=high, entry=entry, outcome=outcome,
                        expected_pair=observed['expected_pair'], trace_digest=result['trace_digest'],
                        scenario_digest=result['scenario_digest'],
                        first_terminal=observed['first_terminal'], max_depth=result['stack']['max_depth']))
                    if keep:
                        witnesses.append(dict(path=name, observed=observed))
            print(f'high={high:02x}: {len(runs)} clean reset runs', flush=True)
    sources = [Path(__file__), HERE/'paired-capture-study.json', HERE/config['mapping'],
               HERE/config['scenario'], HERE/'execute.py', HERE/'common.py',
               HERE/'defined_condition_fit.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts),
        runs=runs, witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Independent external capture bytes survive into paired arithmetic. The previous-zero loop tests only the final high byte; nonzero low-byte results can return. Captures, dispatch and downstream carry reply remain explicit diagnostic stubs, not a recovered physical protocol or DAC output.'))


if __name__ == '__main__':
    main()
