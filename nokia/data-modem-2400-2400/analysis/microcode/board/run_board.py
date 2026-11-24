"""Run a wiring reconstruction without inventing unresolved nets or clock phases."""
import argparse
import json
from pathlib import Path
from engine import Engine, Stop, validate, PORTS, REFERENCE
from decode import write_listing


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')



def run(board_path, scenario_path, out, cycles):
    board = json.loads(board_path.read_text())
    scenario = json.loads(scenario_path.read_text())
    out.mkdir(parents=True, exist_ok=True)
    report = validate(board)
    dump(out/'validation.json', report)
    if report['errors']: raise ValueError('; '.join(report['errors']))
    engine = Engine(board, board_path.parent)
    write_listing(engine, out)
    events = scenario.get('cycle', [])
    completed, stop = 0, None
    with (out/'trace.jsonl').open('w') as trace:
        def record(label):
            row = engine.snapshot(); row['phase'] = label
            trace.write(json.dumps(row, sort_keys=True)+'\n')
        try:
            engine.initialize(scenario.get('initial_inputs', {}))
            record('initialized')
            if not events:
                raise Stop('No evidence-backed clock schedule: '+scenario.get('blocked_reason','cycle events missing'))
            for cycle in range(cycles):
                if str(cycle) in scenario.get('cycle_inputs', {}):
                    engine.step(scenario['cycle_inputs'][str(cycle)])
                    record(f'cycle={cycle} external stimulus')
                for event in events:
                    engine.step(event['set'])
                    for name, ref in board.get('observables', {}).items():
                        # Outputs are diagnosed when explicitly designated observable.
                        if isinstance(ref, str):
                            target,port,bit = REFERENCE.fullmatch(ref).groups()
                            width = (board['external'][port]['width'] if target == 'EXT' else
                                     PORTS[board['components'][target]['type']][1][port])
                            if bit is not None: width = 1
                            if engine.expr(ref,width).integer() is None:
                                raise Stop(f'observable {name} is unresolved')
                    record(f'cycle={cycle} {event["name"]}')
                completed += 1
        except Stop as err:
            stop = str(err); record('stopped; current event may be incomplete')
    summary = {'board':board['name'], 'evidence_status':board['status'],
               'scenario':scenario['name'], 'completed_cycles':completed,
               'events':engine.event, 'stop':stop or 'cycle limit',
               'faithful_nokia_execution':False,
               'unconnected_inputs':report['unconnected_inputs'],
               'limitations':board.get('limitations',[]),
               'interpretation':'A model run, not hardware validation. Connections follow the configuration and its declared evidence status; missing inputs remain unknown.'}
    dump(out/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',type=Path,required=True)
    parser.add_argument('--scenario',type=Path,required=True)
    parser.add_argument('--cycles',type=int,default=1000)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.cycles < 1: parser.error('--cycles must be positive')
    try: result = run(args.board,args.scenario,args.out,args.cycles)
    except (ValueError,KeyError,OSError) as err: parser.exit(2,str(err)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'unconnected_inputs'},indent=2))


if __name__ == '__main__': main()
