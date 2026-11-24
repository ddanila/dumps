# Reset-driven paths establish the shift wrapper's sensitive inputs

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [local caller experiment](DRAIN-CALLER.md) left open whether reset could
reach the wrapper with R7=FF. Seeded dispatch runs now demonstrate that it can,
under the existing fitted-original/previous-flag model. They do not recover
the physical dispatch index or external-input source.

## Register provenance

With dispatch mode `random`, seeds 6 and 14 select entry 1 at 109, reaching
148 via branch 10B. For all 256 constant external D bytes, both seeds establish:

| Point | Observed effect / input |
| --- | --- |
| 074 | R0 becomes 255−D |
| 106/107 | D+R0 becomes FF in R7; 107 is its last writer before the wrapper |
| 14C | R0 becomes D; R12/R13 remain zero |
| 24F | Q becomes R12+R0, hence D |
| 150 | Calls wrapper 248 with R7=FF and Q=D |

The [study](drain_reset_study.py) reconstructs registers from complete traces
and records writes even when the stored value does not change. The 107 write
would otherwise disappear from a change-only provenance analysis. Every run
checks this chain, the dispatch entry, and the composed loop prediction.

## Outcomes with D held constant

Each seed gives the same partition of all 256 D values:

| Outcome | Number of input bytes |
| --- | ---: |
| Wrapper returns; execution reaches terminal 084 | 1 (D=00) |
| Exact repetition in first right-shift loop | 248 |
| Exact repetition in second right-shift loop | 6 |
| Exact repetition in left-shift loop | 1 (D=80) |

The six second-loop cases are D=40, 67, 72, 79, 7D, 7F (hex). These inputs
pass the first loop because some right-shifted value of Q=D makes D+Q=80,
but the reduced Q cannot satisfy that criterion a second time.

Right-loop repetition has period four instructions; left-loop repetition has
period two. The detector compares next PC, all register RAM, Q, ALU results
(including the next carry feedback and previous condition flags), and the full
stack state. No computed dispatch occurs inside the repeated interval. With
constant D and fixed flags these are exact modeled cycles, not timeout guesses.
All 512 executions are clean in the emulator's sense: there are no model or
stack errors. Clean execution does not mean the routine returns.

## Input changes can release the loops

Eight additional diagnostic runs keep the same reset path and first-caller
state but change the external-read stub: 299 reads D once and then zero;
187 reads zero; other addresses still read D. Both seeds, with D=01,40,80,FF,
then return through the wrapper and reach 084 without a repeated loop state.
No PC, register, condition result, or stack entry is injected to force an exit.

This is a counterexample to the claim that loop repetition alone disproves the
field assignment. The model can finish when its external input changes.
Conversely, the constant-input runs show that the earlier non-return cases
cannot be dismissed solely as unreachable register fixtures. Neither the
constant input nor this diagnostic change is a recovered physical protocol.
The result narrows the question to the external D source, dispatch selection,
and condition/datapath hypotheses.

## Reproduce and scope

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/drain_reset_study.py
```

[Configuration](drain-reset-study.json) declares seeds, inputs, limits and the
separate diagnostic stub. The [report](results/drain-reset-study/report.json)
stores 512 constant-input summaries, eight release summaries, register-writer
chains, dispatch choices, repeated states, and source/trace hashes. Ten constant
and eight changing-input witnesses retain complete 1,000-cycle traces.

The fixed-dispatch reset experiments in the earlier caller report still stand:
they do not reach this wrapper. This experiment changes only the declared
scenario dispatch policy and read stub. Default mappings and scenarios remain
unchanged, and no physical DSP algorithm or I/O wiring is claimed recovered.
