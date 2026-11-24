# Input-selected handlers and flag timing

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The [prefix study](SELECTOR-PREFIX.md) established independent Q accumulation
and entry into all eight handlers under q1/q3. This study follows those handlers
through their subsequent execution and tests global flag timing without silently
changing the input schedule to hide a failed initial wait.

## Experiment

[Configuration](handler-timing-study.json), [runner](handler_timing_study.py),
and [report](results/handler-timing-study/report.json) preserve all assumptions.
There are 2,048 zero-reset runs: two mappings, two flag timings, two reply
schedules, and all 256 input sums. Each run executes 512 instructions in the
main integrated emulator, with the actual four-entry stack and defined logical
flags. All runs are clean and execute no unused words.

The inputs at 002 and 076 are A5 and `(Q-A5)&FF`; 109 selects using Q. All other
dispatches use constant index 2 and the existing all-cases tables. Default D is
1. The two early reply schedules are hold-last `[1,0]` at either PLP addresses
117/106 or BLT addresses 118/107. The other pair continues reading default 1.
No optional BRT gate is enabled. Addresses below are hexadecimal.

Every run reaches an exactly repeated modeled state within the bound. The
recurrence key includes next PC, all 16 RAM registers, Q, all ALU flags and Y,
stack pointer, depth and all four stack slots, and every input sequence cursor
saturated at its hold-last phase. ALU carry is also the feedback carry state.
Dispatch is deterministic; logging counters do not affect future execution.
Thus these are persistent modeled loops under these fixed future inputs, not
merely runs that failed to finish within 512 cycles. A future changed external
reply can invalidate that recurrence premise.

## Handler results

With previous flags and PLP replies, each profile has 192 terminal and 64
nonterminal runs. With current flags and BLT replies, each has 160 terminal and
96 nonterminal runs. Each table row represents 32 sums per profile, and both
profiles have the same outcome/period classification across all of them.
“Terminal” means reaching the stable 084 loop, not a physical completion signal.

| Q & 7 | Handler | Previous flags + PLP replies | Current flags + BLT replies |
| --- | --- | --- | --- |
| 0 | 11A | Four-instruction loop in 127–12A | Terminal |
| 1 | 148 | Terminal | Terminal |
| 2 | 18B | Two-instruction poll at 1EC–1ED | Eight-instruction transform loop reached through 3EA |
| 3 | 300 | Terminal | Terminal |
| 4 | 259 | Terminal | Twelve-instruction arithmetic loop |
| 5 | 345 | Terminal | Twelve-instruction arithmetic loop |
| 6 | 09E | Terminal | Terminal |
| 7 | 133 | Terminal | Terminal |

The crossed combinations, previous flags with BLT replies and current flags
with PLP replies, account for 1,024 runs. All repeat the two-instruction
117/118 wait and never execute 109. An unchanged reply schedule would therefore
confound a comparison of downstream handlers under different flag timings.
Even the matched schedules change captured register values; they are complete
scenario alternatives, not an isolated intervention on one branch's timing.

Handler 0 illustrates the timing tradeoff. In q1/q3, 129 exposes R0 and 12A
exposes R0+1 without writing R0. BLT select 0 means nonzero. Previous flags exit
only when R0 is zero; current flags exit only when R0 is FF. Reset reaches this
helper with R0=FF. Changing timing releases this loop, but causes other handlers
to repeat. A larger number of terminal runs is not evidence of hardware truth.

## A nonzero reset overflow path

For Q=FF, handler 133 adds D=1 at 138 and wraps Q to zero with carry. Both
previous-flag profiles then take the actual reset call chain through 3EA,
3D5 and 3C0. This establishes a reset-triggered overflow path, extending the
previous local accumulator fixtures. The transform source registers R10–R13
are zero in these witnesses; this is not a nonzero signal-transform example.

With current flags and BLT replies, q1 skips that chain at 139, while q3 takes
it. The matched reply schedules leave R7=00 for previous timing and R7=FF for
current timing. At 139, q1 computes `0-R7`, while q3 computes `R0-R7`; R0 is FF.
Under current timing, q1 therefore has borrow (carry 0) and branches to 13E;
q3 has carry 1 and continues. Under previous timing, 139 instead tests the
carry from the Q addition at 138. These traces expose both a source-field
ambiguity and a timing/input-state interaction, not a reason to promote q3.

## Verification and next question

The report retains all 2,048 results and hashes of the code, configuration,
mappings and source scenarios. Forty-four complete 512-cycle witnesses cover
every handler under both matched policies, both crossed waits, and Q=FF in
every combination. They replay byte for byte in the main runner. The 89-test
suite includes matched/crossed timing checks and a negative recurrence check:
a still-pending input transition must prevent declaring a terminal recurrence.

The next useful distinction is between external waits that a specified reply
can release and arithmetic loops whose fixed inputs no longer change. The
handler-2 poll at 1EC and the current-timing transform loops provide concrete
states for that investigation. No annotation count or hardware-fidelity claim
is increased by this study.

Reproduce:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler_timing_study.py --out /tmp/nokia-handler-timing
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
