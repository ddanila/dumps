# Startup: preparation, two byte waits and handler selection

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The startup path through 100–109 composes two preparation helpers, two
external-byte waits and an eight-way dispatch. Its complete register state at
handler entry is predictable under q3. The wait-control bytes and the retained
capture bytes have distinct roles, and the transient ALU result before dispatch
does not select the handler in the declared Q-indexed scenario.

## Declared input schedule

Start with zero RAM/Q, q3, previous flags and the established selector-5 true
path from 003 to 100. Let the independent reads at 002 and 076 sum modulo
256 to code c. Define these additional inputs:

| Input site | Supplied values |
| --- | --- |
| 115 | a1 on the first call, a2 on the second |
| 117 | k1 nonzero replies, then zero |
| 118 | Independent capture byte r |
| 106 | k2 nonzero replies, then zero |
| 107 | Independent capture byte s |
| 108 | Independent transient operand w |

The nonzero reply bytes may have any value from 01 through FF. Sequence ends
hold their last value. These are logged diagnostic schedules; no controller
channel, physical handshake or power-on clearing behavior is assigned.

## Preparation and real calls

100 copies zero R15 into R2. 101 calls [06F](RESET-HELPERS.md), which makes
R0=FF from zero R9, copies zero R8 into R2, and adds D076 into Q. Thus Q=c.
The direct calls at 102 and 104 both invoke [112](RESET-HELPERS.md): they
leave R2=1, preserve Q=c and set R4=(c+D115)&FF. The first R4 capture is
therefore replaced by the second after the first external wait returns.

103 calls 117 with a real return frame. 119 returns to 104 and exposes the
first R4 capture on Y without changing it. Its zero-plus-R4 operation clears
carry, regardless of the earlier wait's last capture value. After the second
112 call, 105 branches to 106 without a surrounding call frame. The transient
sums at these call/branch instructions do not replace RAM or Q.

## The two waits

Both instruction pairs perform D+R0 with R0 fixed at FF. The result is
(D-1)&FF and carry is one iff D is nonzero. The destination differs:
117/118 store into R6, while 106/107 store into R7. Their Y output is the
unmodified A input, FF, rather than the stored arithmetic result.

Each PLP pushes its own address. Its following BLT tests the **previous carry
from PLP**, consumes that loop frame, and either branches back to PLP or falls
through. The BLT instruction also executes its own independent capture read:

- A nonzero PLP-side reply repeats the loop, regardless of the BLT-side byte.
- A zero PLP-side reply exits, even if the BLT-side byte produces carry one.
- The BLT-side write replaces the PLP-side write on every iteration, so final
  R6=(r-1)&FF and R7=(s-1)&FF.

Thus r=s=0 captures FF in both registers without preventing release. Conversely,
r=FF captures FE and produces carry one, but a zero at 117 still returns.
This distinguishes loop control from the last captured value.

The first wait has the caller frame from 103 plus one loop frame, giving
maximum depth two. 119 consumes the caller frame. The second wait uses only
its loop frame; dispatch begins with no active frame. No return stack entry is
injected or repaired.

## Dispatch and complete entry state

After the second wait, the carry from 107 is one iff s!=0. 108 exposes
Y=(w+c+int(s!=0))&FF without storing it. 109 exposes (c+1)&FF, but its
declared index source is Q=c. It selects 10A+(c mod 8), whose branch enters:

| c mod 8 | Handler entry |
| --- | --- |
| 0 | 11A |
| 1 | 148 |
| 2 | 18B |
| 3 | 300 |
| 4 | 259 |
| 5 | 345 |
| 6 | 09E |
| 7 | 133 |

At that boundary Q=c, with complete RAM state:

| Register | Value |
| --- | --- |
| R0 | FF |
| R2 | 1 |
| R4 | (c+a2)&FF |
| R6 | (r-1)&FF |
| R7 | (s-1)&FF |
| All others | 0 |

Neither a1 nor w survives in this state. The original split between D002 and
D076 also does not matter once their wrapped sum c is fixed. In particular,
c=FF can make the 109 ALU result zero while still selecting handler 7.

The first 117 executes at cycle 22; 119 executes at 24+2*k1. The first 106
executes at 32+2*k1. Handler entry is reached after **37+2*(k1+k2)** executed
microinstructions. The standard k1=k2=1 schedule therefore gives cycle 41,
as used by the existing handler studies. These counts do not establish a
physical sample rate or command duration.

## Held waits and validation

If either PLP-side input stays nonzero, that pair forms a period-two state
recurrence and dispatch is never reached in the modeled deterministic system.
The first held wait never reaches 119; the second never reaches 108. Recurrence
checks include RAM/Q, all flags, stack slots and saturated input cursors, rather
than inferring a hang from a finite trace alone.

The actual PLP/BLT arithmetic is checked locally for every poll/capture byte
pair at both waits: 131,072 cases with nonzero unrelated RAM and varying Q.
The check verifies carry, Y, the stored result, full RAM preservation and Q.

There are 6,144 zero-reset prefixes spanning all 256 codes, three delay pairs,
four capture pairs and two first/second load pairs. Each stops immediately
before the chosen handler executes and checks the complete state, both loop
counts and branch decisions, helper captures, Y108, Q-based selection and
stack depth. These are complete startup prefixes, not full handler runs.
Eighteen held-wait controls cover every handler index and code FF. Ten saved
witnesses include eight returning prefixes and both held waits.

Regression tests add independent random bytes, delays and nonzero failure
replies; vary a1, w and the initial input split while requiring the same entry
state; and prove both held recurrences. All witnesses replay byte for byte.
Current-flag timing, other initial RAM, other dispatch sources and physical
input relationships remain outside this contract.

[Configuration](startup-contract.json), [runner](startup_contract.py),
[report and witnesses](results/startup-contract/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/startup_contract.py
```
