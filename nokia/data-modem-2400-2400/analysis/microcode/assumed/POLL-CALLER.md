# Caller establishes a successor-byte poll

The [1EC poll](POLLING.md) has a traceable target in the original-register,
previous-flag reset scenario. Its caller does not simply wait for a fixed 01.
The zero-input fixture is one instance of this sequence:

1. At 18D, read external byte X and compute D+Q with carry zero. Q is zero on
   this path, so R3 becomes X.
2. At 19C, compute `~R3 + carry`, with carry zero, and write R4. Thus R4 becomes
   `255-X`. This is the last R4 write before the poll, despite intervening calls.
3. At 1EC, compute `D+R4` modulo 256 and repeat while its previous zero flag is
   false. The successful response is therefore `(X+1) modulo 256`.

R3 is overwritten between 19C and the poll; the comparison survives in R4.
The provenance checker counts every decoded RAM write, including writes whose
value does not change. Looking only at trace register deltas would miss the
zero-valued input write at 18D.

## Exhaustive input experiment

The [configuration](poll-caller-study.json) varies X over all 256 bytes. Each
value gets two 400-cycle reset runs, retaining all other policies and inputs:

- A successor response at 1EC: all 256 runs return through 1EE and finish at 084.
- An unchanged response X: all 256 runs remain in the poll without returning.
  The sum is FF for every X, so this response cannot satisfy the comparison.

All 512 runs complete without stack violations. Wraparound works: initial FF
requires response 00. The saved report checks the writes at 18D and 19C and the
last-writer relationship at 1EC for every run.

Input changes also affect intervening execution. There are 32 distinct complete
control paths across the two response types, not a single fixed-duration path.
For example, the first poll is at cycle 188 for X=00, 202 for X=01 or 7F, 200 for
X=80, and 174 for X=FF. These are emulator cycles under the scenario, not a
physical sampling period. The report retains the first control-path difference
from the corresponding X=00 run and groups values with identical paths.

A provisional name is **successor-byte wait**. A counter-change handshake or
sample boundary is a possible interpretation, but neither is established:
18D and 1EC are instruction addresses, not identified ports, and their supplied
bytes are separate explicit stubs. The experiment does not prove they read the
same hardware source. It also does not generalize Q=0, carry=0, or this path to
other condition policies, register layouts, or inputs elsewhere in the program.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/poll_caller_study.py
```

[Report](results/poll-caller-study/report.json) records all 512 results and their
trace digests. Full traces, mappings, scenarios, and summaries are retained for
X=00, 7F, and FF with both responses. The provenance unit test specifically
covers unchanged-value writes. The program listing scopes these interpretations
to the fitted original-register profile and states the scenario restrictions.
