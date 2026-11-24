"""Compare executed controller countdowns with V.26ter timing windows."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
MATRIX=HERE/'results/state-matrix.json'
ITU='https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I!!PDF-E&lang=e&type=items'
RELOAD_MS=(65536-0xfc21)*12/11980800*1000

# Standard windows are from V.26ter (11/88) §§6.3.1.1–6.3.1.3. State names
# below are alignment hypotheses, not decoded firmware stage names.
COMPARISONS=(
    ('A0',1805,'answer initial silence',1800,2500,'6.3.1.1.2'),
    ('A1',2605,'answer 2100 Hz tone',2600,4000,'6.3.1.1.2'),
    ('A2',60,'answer post-tone silence',55,95,'6.3.1.1.2'),
    ('A7',250,'rate-selection silence',245,255,'6.3.1.2'),
    ('AA',580,'500 ms tone plus 75 ms silence combined',505,645,'6.3.1.2.2'),
    ('AB',25,'post-echo-training silence',22,28,'6.3.1.3'),
    ('B8',70,'75 ms silence candidate',55,95,'6.3.1.1.2'),
)


def run():
    matrix=json.loads(MATRIX.read_text())
    states={row['state']:row for row in matrix['rows']}
    rows=[]
    for state,expected,label,minimum,maximum,section in COMPARISONS:
        loaded=states[state]['reload']['countdown']
        assert loaded==expected,(state,loaded,expected)
        raw=loaded*RELOAD_MS
        rows.append(dict(state=state,loaded_ticks=loaded,candidate_stage=label,
                         standard_section=section,standard_window_ms=[minimum,maximum],
                         raw_reload_period_duration_ms=raw,
                         nominal_1ms_tick_duration_ms=loaded,
                         raw_in_window=minimum<=raw<=maximum,
                         nominal_in_window=minimum<=loaded<=maximum,
                         local_expiry_next=states[state]['expiry']['next_state']))
    assert all(row['nominal_in_window'] for row in rows)
    return dict(status='timing-consistency comparison; state roles unproven',
        standard=ITU,controller_rom_sha256=matrix['controller_rom_sha256'],
        state_matrix_sha256=hashlib.sha256(MATRIX.read_bytes()).hexdigest(),
        timer=dict(reload='FC21',oscillator_hz=11980800,
                   raw_reload_to_overflow_ms=RELOAD_MS,
                   nominal_software_tick_ms=1.0),rows=rows,
        interpretation='Seven selected countdowns fit V.26ter windows at a nominal 1 ms software tick. The raw hardware reload period alone puts A0 and A1 just below the corresponding lower bounds; ISR/reload overhead is not measured.',
        limitations=['The rows are timing hypotheses chosen from many firmware states; no stage output signal is observed here.',
                     'A6=2000 ticks resembles the standard 2 s rate-pattern timeout but no tolerance window is specified, so it is not scored in the table.',
                     'AA=580 is compared with a combined tone-plus-silence window, not proof that one state produces both signals.',
                     'The state matrix runs are local fixtures with other inputs held zero; continuous call behavior and physical DSP commands remain unverified.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/sequence-alignment.json')
    args=parser.parse_args();report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print([(row['state'],row['loaded_ticks'],row['nominal_in_window'],row['raw_in_window'])
           for row in report['rows']])


if __name__=='__main__':main()
