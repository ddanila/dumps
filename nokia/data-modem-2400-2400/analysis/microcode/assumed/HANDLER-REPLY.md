# Handler 2: external reply versus an invariant loop

The [timing comparison](HANDLER-TIMING.md) left handler 18B repeating under
both timings, at different locations. This follow-up identifies a specific
reply that releases the previous-flag path and proves why later external
replies cannot release the current-flag path under the retained table decode.

## Previous flags: input-dependent comparison and completion

All 32 input sums `s = 2, 10, ..., 250` select handler 2 through Q at 109.
The reset inputs remain A5 at 002 and `(s-A5)&FF` at 076. Early replies are
`[1,0]` at 117/106; other D defaults to 1. All other dispatch indices stay 2.
Only the subsequent read sequence at 1EC changes within each comparison.

| Quantity | q1 | q3 |
| --- | --- | --- |
| First 1EC cycle (zero based) | 186 | 185 |
| R4 and R12 on entry to poll | `(s-2)&FF` | FE |
| Unique release byte | `(2-s)&FF` | 02 |
| First 084 cycle with immediate release | 218 | 217 |
| R12 at terminal loop | `(s-2)&FF` | FE |

These identities hold for every tested sum, not arbitrary initial registers or
input schedules. The first poll states preserve the real reset stack and
registers. All 256 possible input bytes are evaluated at each of those 64
states, giving 16,384 arithmetic checks. Both profiles decode 1EC as
`R3 = (D + R4)&FF`, with R4 on Y. The following previous-zero BLT repeats while
the sum is nonzero. Only `D = -R4 mod 256` releases it. R4 and Q are unchanged
by the poll body. This extends the earlier fitted-original
[poll interpretation](POLLING.md) to two independent decodes and nonzero-input
reset paths.

For each state, four complete runs test default 1 held forever and release
after zero, one, or seven default replies. Default 1 never matches these R4
values. Every releasing run returns through 1EE and reaches 084. Each failed
reply adds exactly two instructions: first 1EE is `first_poll + 2*delay + 2`,
and first 084 is `first_poll + 2*delay + 32`. Traces before the first poll are
identical within each comparison. R12 retains the value copied from R4 at 3A3;
this is surviving internal data, not an identified external output.

This is a testable distinction between source-field candidates: q1 retains an
input-dependent comparison value, while q3 collapses these 32 input sums to a
fixed value. Neither behavior establishes which candidate matches the board.

## Current flags: no later D reply or table choice can release it

With current flags and matched BLT replies at 118/107, all 64 reset runs reach
3EA with `R0 = Q = s`, where s is nonzero. They never reach 1EC.

The runner checks an invariant directly against the decoded words:

- 3EA–3ED preserve R0 and Q. At 3ED the ALU computes `R0 & Q`; the current-zero
  condition repeats when this value is nonzero.
- The four candidate calls from 3EC enter 3EF, 3F3, 3F7, or 3FB. Each executes
  three straight instructions followed by POP. None writes R0 or Q.
- The call at 3EC is unconditional under the retained scenario policy.

Consequently, every iteration tests the same nonzero s. Arbitrary later D
values and any sequence of choices among those four entries cannot release
this loop. This conclusion is stronger than a bounded constant-index trace.
It does not cover different table targets, a changed register decode, changes
to the condition source, or unmodeled hardware writing registers. The proof
rejects mutated table instructions that write either R0 or Q.

Previous flags test the last table instruction instead, so this invariant does
not prohibit their observed return. A later byte reply suffices for the
previous-flag poll; explaining current-flag completion requires changing an
earlier state or a retained structural assumption. This gives a concrete
constraint for the next decode investigation.

## Artifacts and checks

[Configuration](handler-reply-study.json), [runner](handler_reply_study.py),
and [report](results/handler-reply-study/report.json) retain the assumptions,
64 poll states, 64 current-timing transform entry states, 256 reply outcomes,
source hashes and eight full witness traces. There are 384 full reset runs
including the unchanged previous/current baselines. All execute 384 cycles
cleanly with no unused words. Eight witness directories cover both profiles,
small/large sums and held/delayed replies.

The 90-test suite checks reply timing, unchanged prefixes, surviving R12, and
negative mutations of the loop invariant. The full study reproduces byte for
byte. Physical input channels, write strobes, DAC samples, and the controller
protocol remain unidentified by this experiment. No new distinct addresses
are counted as annotated; existing interpretations gain profile-specific
reset evidence.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler_reply_study.py --out /tmp/nokia-handler-reply
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
