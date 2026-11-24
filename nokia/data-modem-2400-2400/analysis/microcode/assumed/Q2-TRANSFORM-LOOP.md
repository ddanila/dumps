# q2's 3C0 wrapper repeats a fixed transform until its high-byte test passes

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

With a constant dispatch index and the shared previous-zero condition policy,
3C0 is an idempotent transform loop: it repeatedly transforms the same source
pair, writing the same result to R4–R7. It returns only when the second output's
high byte is zero. It does not progressively reduce or shift its source data.

The [accumulator study](Q2-ACCUMULATOR.md) identified a carry-triggered call
from 13D. This [follow-up](q2_transform_loop_study.py) executes that real call,
its nested table call, loop branch and return, rather than forcing the wrapper
to run once. The retained q2 mapping, previous flags and fixed table index are
explicit hypotheses; this is not a recovered physical loop condition.

## Data and termination

Let X=R10+256*R11 and Y=R12+256*R13 on entry. The existing quarter-turn table
writes A to R4/R5 and B to R6/R7, with arithmetic modulo 65536:

| Entry | Table | A | B | Return condition |
| --- | --- | --- | --- | --- |
| 0 | 3C5–3C8 | X | Y | Y is 0000–00FF |
| 1 | 3C9–3CC | −Y | X | X is 0000–00FF |
| 2 | 3CD–3D0 | −X | −Y | Y is 0000 or FF01–FFFF |
| 3 | 3D1–3D4 | Y | −X | X is 0000 or FF01–FFFF |

Values and ranges in this table are hexadecimal. BLT at 3C3 tests the zero
flag from the last table instruction, which wrote the high byte of B into
R7. Thus B=0001 and B=00FF return just as B=0000 does. B=0100 does not return.
It would be incorrect to describe the condition as an entire 16-bit zero test.

The wrapper also copies R0 to R1. It preserves Q and all RAM except R1 and
R4–R7, including its source pair R10–R13. Instruction 3C1 computes D−R11 but
does not store it. With scenario-supplied constant dispatch, that value does
not affect which table entry runs; the table replaces its flags before the
loop test. This conclusion does not apply automatically to a datapath-indexed
or changing-index dispatch scenario.

A successful call takes **10 instructions**, counting 13D through the return
at 3C4. A failing call repeats an **eight-instruction cycle** at 3C0. The probe
observes two completed iterations to verify identical RAM, Q, ALU/previous
carry and complete sequencer stack state; it does not classify repetition
from a timeout. No external-input byte change alone can alter these fixed-index
results under the selected decode, because D has no surviving effect before
the table's high-byte test.

## Checks

The checker compares the complete RAM array, Q, return destination and cycle
counts against an arithmetic reference for **263,344 local cases**:

- For each of four entries, all 65,536 values of the source word controlling
  the last high byte. The other word is varied by a declared deterministic
  formula. Each entry has 256 returns and 65,280 repeating cases in this sweep.
- All pairs from ten byte/sign boundary words, each with Q=00,55,FF and a
  corresponding external D fixture: another 1,200 cases.

This exhausts the controlling-word domain, not all 2^32 source pairs. Twelve
integrated witnesses check return with zero B, return with nonzero B, and
repetition for every entry. Their instruction PCs, ALU results and tests match
the component probe exactly.

Forty additional integrated fixtures start at 133 with Q=1, R7=2 and D=FF.
The accumulator addition carries and leaves Q=0; old Q<R7 selects 13D without
calling 3EA or 3D5. These runs therefore reach the wrapper through its actual
arithmetic gate, with no injected branch or synthetic return. Twelve reach
terminal 084 and 28 remain in the wrapper. All final RAM and Q values match
the composed prefix/transform reference. These are **local nonzero-Q fixtures**,
not a claim that reset reaches these states.

## What remains open

The arithmetic tables were originally selected partly for their quarter-turn
identities. This wrapper study adds independent control-flow and state-retention
constraints; it does not independently establish the source-bit mapping.
A loop that cannot change its own failure condition may indicate an external
condition or changing dispatch on the board, or a wrong decode/flag assumption.
Its inability to terminate for most local operands is recorded as a constraint,
not treated as proof that the physical modem hangs. Physical output consumers
and the meaning of the source pair remain unknown. No default mapping changes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q2_transform_loop_study.py
```

[Configuration](q2-transform-loop-study.json) records fixtures and assumptions.
The [report](results/q2-transform-loop-study/report.json) contains counts,
comparison digest, local witnesses, caller outcomes and source/trace hashes.
All 40 caller traces and 12 local traces are retained in full.
