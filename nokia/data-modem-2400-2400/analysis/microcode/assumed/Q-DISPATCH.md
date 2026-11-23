# Q input, computed dispatch and the zero tail

A reset execution now reaches 2CF under q2 and the optional BRT gate. Starting
from the [index-12, D=01 witness](DISPATCH-RANGE.md), change only the external
read at 2A8 to zero. That instruction loads Q; Q remains zero through the
26F dispatch and 2CD. Gated 2CE sees the actual previous zero flag and falls
through into 2CF. The run continues through 2D0 and 2D9–2DB to terminal 084.
No branch outcome, register value or return address is injected.

## Input dependency experiment

`q_dispatch_study.py` varies the read byte at 2A8 over all 256 values and
compares four existing dispatch sources at 26F. The rest of the q2 reset
scenario stays at global constant index 12 and default D=01, including the
early zero replies at 117/106 and the optional BRT gate. This is a diagnostic
PC-keyed input stub, not an identified hardware channel.

All 1,024 runs are clean and reach 084 within 256 cycles.

| Source at 26F | Visited-word union | Runs reaching 2CF | Runs reaching 3BD–3BF |
| --- | ---: | ---: | ---: |
| Scenario constant 12 | 175 | 1 | 255 |
| Q | 215 | 0 | 128 |
| Current Y | 110 | 0 | 0 |
| Previous Y | 215 | 0 | 128 |

These are unions across runs, not coverage of one execution. Q and previous Y
produce identical complete traces apart from the logged dispatch-source name;
the script checks this for every input byte. At 26E, R1 is zero in these runs,
so its Y equals Q. At 26F, the current ALU operation is zero AND Q, hence
current Y is always zero. Using it selects entry zero for every input.

With the Q/previous-Y source, the 16-entry table is indexed by Q modulo 16.
The target frequencies across all byte values are:

| Target | Runs |
| --- | ---: |
| 200 | 112 |
| 2C6 | 48 |
| 230 | 32 |
| 280 | 32 |
| 217 | 16 |
| 2CB | 16 |

This exposes a dependency the conservative graph cannot represent: Q=0
selects 2C6, while the direct 2CB entry requires Q modulo 16 equal to 12.
None of the alternative paths in this sweep reaches 2CF either. The constant
index allows 2CB with Q=0, so its zero-tail witness is valid under that stub
but is not evidence for a physical Q-driven dispatch source.

## Interpreting 2CB–2CF

Along these reset paths, R0=FF and the Q byte loaded at 2A8 survives to 2CE.
The script verifies that every observed 2CE follows 2CD, whose ALU result is Q.
Under the optional gate and previous-zero policy, 2CE therefore branches to
204 exactly when Q is nonzero, otherwise falls through to 2CF.

2CB exposes `~R0 & R7`; with R0=FF its result is zero. If execution visits
2CC, it exposes Q−1 and its skip tests the preceding zero result, so 2CD is
not skipped. 2CD exposes Q. None of these instructions changes RAM or Q.
2CE exposes `R0 & Q`, but its branch uses the preceding result from 2CD.

In the Q=0 witness, 2CF exposes D+Q+carry = 01+00+0 = 01 without changing
RAM or Q. The script checks that result and the absence of register changes.
The following instruction 2D0 loads a fresh Q value (01) and begins the
previously studied paired drain sequence. Thus the newly visited word exposes
a transient arithmetic result; its external consumer is still unidentified.

## Why the other tail does not branch to 287

For every run in this sweep that reaches 3BC, the script checks that the last
Q writer is 2F3, Q is zero, R0 is FF, and 3BB has just produced zero.
2F3 computes zero AND R0 into Q, erasing the earlier 2A8 input. The tail
therefore always receives the (FF,00) pair from the
[conditional-tail analysis](DISPATCH-RANGE.md), executes 3BD and 3BE, and falls
through from 3BF to 3C0. Varying the earlier Q byte cannot change this exit
along the observed paths. No run visits 286 or 287–28A.

The saved shortest structural witness to 287 takes 26F→200→281. Under q2,
26F always produces zero, so gated 200 must instead fall through to 201.
That particular witness cannot execute with these actual flags, regardless of
the Q byte. This rules out that path, not every possible entry into 287.

Together with the preceding studies, integrated reset witnesses now cover
eight of the 12 words added by the optional gate: 0FA, 2CF, 2D9–2DB and
3BD–3BF. The four words 287–28A still have only structural/local entry evidence.
Default reachability labels remain unchanged; the gate and dispatch source
are hypotheses, and physical I/O remains unresolved.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q_dispatch_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [report](results/q-dispatch-study/report.json) records every case, selected
branch events with preceding flags and Q-writer provenance, trace digests,
source hashes and 20 complete witnesses. The fixed input-byte sweep is
exhaustive only within the stated reset scenario, mapping and source options.
