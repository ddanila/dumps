# Q shifting with input-dependent termination at 296

Routine 296–29E shifts Q right while placing an input-dependent sequence in R0.
Under the selected fitted-original mapping and previous-flag policy, reaching
Q=0 does **not** guarantee return. This supplies a new constraint on that
hypothesis; it does not establish a multiply or divide algorithm.

## Derived behavior

The local probe starts at the actual BSR at 249 and stops on return to 24A,
or when the complete machine state repeats at 298. External D is constant,
shift fill is zero, and R13=A5. Other initial registers come from the existing
[previous-flag polling scenario](POLLING.md), with R7 supplied as 00 or FF.

296 and 297 write `(Q-D) mod 256` to R0. The loop then does:

1. At 299, set R0 to `2*(D+Q) mod 256`.
2. The carry from that addition selects the branch at 29A. When D+Q≤255,
   the branch goes directly to 29D; its preceding zero flag comes from
   `R0 AND R7`.
3. When D+Q>255, execute 29B/29C. Their result supplying the loop's zero
   flag is `(D+Q+bool(D AND Q)) mod 256` under the defined logical-carry model.
4. At 29D, write `((R13+old_Q) mod 256) >> 1` to R0 and shift Q right once.
   BLT uses the **previous** zero flag, so this new arithmetic result does not
   decide whether the loop repeats.

Only R0 and Q change in these fixtures. With R7=FF, return occurs exactly when
some value in `initial_Q, initial_Q>>1, ..., 0` makes D+Q equal 0 or 128.
The overflow arm cannot satisfy the required zero condition. With R7=00,
return instead occurs at the first iteration where D+Q≤255, which must occur
by the time Q reaches zero.

For a returning case, cycles from caller 249 through POP 29E are
`4 + 4*iterations + 2*overflow_iterations`. The final Q is half the terminating
iteration's Q, and final R0 follows the biased-shift expression above.

## Exhaustive local result

| R7 | D/Q combinations | Return | Exact repeated state |
| --- | ---: | ---: | ---: |
| 00 | 65,536 | 65,536 | 0 |
| FF | 65,536 | 2,177 | 63,359 |

Every non-returning case reaches the four-instruction cycle
`298 → 299 → 29A → 29D → 298`, with Q=0. R0 alternates between `2*D mod 256`
and `R13>>1`. Repetition is detected using PC, stack pointer and contents,
all register RAM, Q, carry feedback, and preceding ALU results. It is not
inferred from an expired cycle budget.

The [study](biased_drain_study.py) compares all 131,072 cases to the closed-form
termination criterion and final state. Six witnesses also run through the
ordinary integrated executor, checking final PC/RAM/Q and retaining full traces.
Their inputs include successful and repeating paths, both masks, and overflow
iterations. The [report](results/biased-drain-study/report.json) contains the
counts, digests, source hashes, exact repetition periods and witnesses.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/biased_drain_study.py
```

## Implication for the model

A generally terminating interpretation needs suitable caller values, changing
external input, or a different field/condition hypothesis. The real caller's
R7 and external channel have not been established, so these local fixtures do
not disprove the whole mapping or demonstrate a hardware hang. They do reject
calling this an unconditional Q-drain helper under arbitrary inputs. The
current scenario and default decode remain unchanged; this result is evidence
for subsequent caller and condition-source work.
