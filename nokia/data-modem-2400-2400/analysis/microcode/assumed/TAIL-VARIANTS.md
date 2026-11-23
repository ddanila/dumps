# A retained alternative reaches the excluded tail

**q3 reaches 287–28A from reset** with the same index-12, D=01 inputs used by
the q2 witness. The [q2 exclusion argument](TAIL-EXCLUSION.md) remains valid:
q3 changes the operations at 3BD–3BE, so the argument's final arithmetic step
no longer applies. This is a useful distinction between retained decodes,
not a reason by itself to promote q3 as the physical wiring.

## Matched reset runs

`tail_variant_study.py` executes all six retained mappings with the same
zero-reset scenario, optional composed BRT gate, constant dispatch index 12,
and all 256 default D bytes. Reads at 117 and 106 supply D then zero, as in the
preceding studies. Every run lasts 256 cycles and uses actual datapath flags.
All 1,536 runs are clean.

| Mapping | Terminal at 084 | Nonterminal at bound | Visited-word union | Newly graph-added words reached |
| --- | ---: | ---: | ---: | --- |
| q1 | 1 | 255 | 171 | None |
| q2 | 1 | 255 | 159 | 3BD–3BF |
| q3 | 1 | 255 | 144 | 287–28A, 3BD–3BF |
| q4 | 1 | 255 | 159 | 3BD–3BF |
| fitted_original | 0 | 256 | 51 | None |
| fitted_swapped | 256 | 0 | 119 | 2CF, 2D9–2DB |

For q1–q4, the only terminal case is D=01. That is also the only case reaching
the listed new words for q2–q4. fitted_swapped reaches its listed words at
every D byte. Nonterminal at the bound does not establish an infinite loop.
The unions are over multiple runs, not one continuous execution.

## The decisive difference is subtraction, not Q preservation

q3 and q4 decode 2F3 as D AND Q into Q, whereas q2 clears Q with zero AND R0.
However, in the D=01 witnesses, all three arrive at 2F3 with Q=02; the mask
still produces Q=00. Thus this source-field difference does **not** explain
the observed q3 branch. The script checks that q2, q3 and q4 all enter 3BC
with R0=FF and Q=00.

| Instruction | q2/q4 expression | q3 expression |
| --- | --- | --- |
| 3BC | `~(R0 xor Q)` | Same |
| 3BD | `Q−R0` | `Q` |
| 3BE | `Q−R0−1` | `Q−1` |
| 3BF | `R0 & Q`; branch on preceding zero | Same |

3BC produces zero, so 3BD does not skip 3BE. In q2/q4, 3BE produces 00 and
3BF falls through to 3C0. In q3, 3BE produces FF and 3BF branches to 287.
The script asserts these actual values and next PCs, rather than inferring
the cause only from visited-word sets.

In the q3 reset witness, the successive ALU results at 287, 288, 289 and 28A
are FF, 00, 01 and 00. None changes RAM or Q. Execution continues at 28B and
ultimately reaches 084. All calls/returns use the existing live stack.

## Local q3 interpretation

`q3_tail_study.py` checks all 65,536 R0/Q pairs using the actual datapath and
sequencer models, with previous zero set on entry to 3BC. Let A=R0 and q=Q:

- 3BD exposes q and skips 3BE unless q is the bitwise complement of A.
- If executed, 3BE exposes q−1.
- 3BF branches to 287 when the preceding result is nonzero, otherwise to 3C0.

Consequently, 3C0 is selected for the 255 pairs q=0, A≠FF and for the single
pair (A,q)=(FE,01). The other 65,280 pairs select 287. RAM and Q are preserved.
These local pairs are not all claimed reachable from reset.

The four-word tail at 287–28A exposes, modulo 256:

| Address | q3 ALU result |
| --- | --- |
| 287 | Q−1 |
| 288 | Q |
| 289 | R2−R0 |
| 28A | R12−R0−1 |

Every instruction is a no-load operation. Separate local checks cover every
(R0,R2) and (R0,R12) byte pair and every Q byte, checking the expressions and
unchanged full RAM/Q. The operations do not store intermediate values or
share destination registers, so these pairwise domains cover their operands.
Their external output consumer remains unidentified.

## Scope of the result

Across this and earlier studies, all 12 words added by the optional gate now
have integrated reset witnesses: 0FA, 287–28A, 2CF, 2D9–2DB and 3BD–3BF.
This statement combines explicitly different mappings and input scenarios;
it is not evidence that one mapping executes all of them, nor an execution
of the whole program under one recovered hardware model.

The q2 exclusion still rules out 287–28A within its stated assumptions.
The alternative q3 arithmetic supplies a concrete route that breaks that
exclusion. Default reachability labels remain unchanged, and ten other used
words remain outside even the optional gated structural graph. Physical I/O,
algorithm interpretation and the full plan remain incomplete.

## Reproduce

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/tail_variant_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q3_tail_study.py
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/program_reading.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```

The [reset report](results/tail-variant-study/report.json) contains every case,
selected instruction states, decoded operations, source hashes and seven full
witnesses. The [local report](results/q3-tail-study/report.json) records the
exhaustive local checks and representative examples.
