# Early entry 013: an input-carry wait followed by a fixed-register wait

The early table's entry three reaches 013 from zero reset. Under q3 and
previous flags, its call into 01E deliberately enters a loop through the BLT
instruction. The initial call supplies a real stack frame; subsequent passes
use the adjacent PLP at 01D. An external reply at 01D can release this loop.
The later loop at 05D has a different, fixed-register predicate.

This study retains the explicit early-table index, selector-5-false boot,
and table assumptions from [EARLY-WAIT.md](EARLY-WAIT.md). No PC or stack
state is injected into the reset runs.

## Captures and discarded preparation

008 has already set Q=FF. Define d13=D013 and u=D014. Then:

- 013 writes R14=(254-d13)&255.
- 014 writes R0=u AND FF=u. Its defined logical carry is one.
- The previous-carry branch at 015 is therefore false; 016 executes.
- 018 copies R0 into Q, replacing FF with u.
- 019 temporarily masks u into R3, but 01B clears R3.
- 01A adds b=D01A, leaving Q=(u+b)&255.

The temporary R2 from 016 is overwritten by the loop. R14 survives the loop,
the subsequent wait and the terminal tail. These formulas use the established
defined logical-carry model; they are not claims about recovered board wiring.

## Why the initial call is balanced

01C calls **01E**, pushing return address 01D. Its zero-AND-Q operation uses
carry input one and produces carry one. Thus the first 01E tests true under
previous-carry timing and branches to the popped return address 01D, regardless
of the arithmetic carry produced by 01E itself.

01D now performs the normal PLP push. The following 01E BLT pops that frame,
returning to 01D if the preceding addition carried, or falling through to 01F
if it did not. The stack is balanced on every pass, with maximum depth one.
This supplies a dataflow explanation for the unusual call-fed loop entry,
not merely a control-flow exception for the static listing.

## Which external reply matters

Both 01D and 01E compute R2=(D+u)&255 while exposing u on Y and preserving
R0 and Q. Their D values can be independent. With previous flags, the test
at 01E uses **01D's** carry:

```
repeat iff D01D + u >= 256
return iff D01D < 256-u
```

D01E changes the transient R2 value and its own flags, but not this branch
predicate. The next PLP uses mapped carry zero, so D01E's carry does not feed
the next tested addition either. R2 is later overwritten at 05F.

For u>0, holding D01D=256-u causes an exact two-instruction recurrence.
Supplying zero releases it. Each unsuccessful PLP/BLT pass adds two cycles.
For u=0, no byte reply can carry: the first PLP/BLT pass always returns, even
if the supplied sequence intended to delay it. The mandatory initial
call-to-BLT trip still occurs in every case.

The study checks all 65,536 u/reply byte pairs. Exactly 32,896 pairs return
and 32,640 carry. This is an input-dependent wait, unlike the later 05D loop.

## Continuation and complete retained state

After release, 01F sets Q=(u+b-f-1)&255, where f=D01F. 020 exposes zero and
021 branches to 059. There Q is replaced with p=D059, discarding the preceding
sum/difference. 05B then writes R4=(p+x)&255, where x=D05B.

Let k be the number of unsuccessful PLP/BLT passes actually executed: zero
when u=0, otherwise the declared release delay. The first 05D cycle is 38+2k.
R3 is zero, so the previous-zero predicate at 05D returns exactly when p=0.
A nonzero p gives an exact seven-instruction recurrence, with final stable
RAM/Q values:

```
Q=p; R0=(p+1)&255; R4=(p+x)&255; R14=(254-d13)&255
all other RAM registers zero
```

For p=0 the terminal tail executes. With y=D064, its complete state is:

```
Q=0; R0=R2=1; R3=(y-1)&255; R4=x; R14=(254-d13)&255
all other RAM registers zero
first 084 cycle = 56+2k
```

If the earlier carry wait is held, neither 01F nor 05D is reached. R0=u,
Q=(u+b)&255 and R14 is preserved. R2 alternates between the two input-addition
results; the complete modeled state repeats after two instructions. No wait
is reported as a physical device acknowledgment or completion signal.

## Verification

The full study runs 1,536 reset cases: every captured u byte, immediate release,
three failing replies followed by release, and a held reply, each with p=0 or
p=1. Other bytes vary with u; independent randomized regressions break those
correlations and test additional p values and delays. The u=0 special case is
checked against all three reply policies.

Each run verifies the actual initial stack trip, captured/overwritten Q
values, full final RAM/Q, delay or recurrence, and maximum stack depth.
Eight saved witnesses cover u=00/FF, held and released carry waits, and the
later fixed-register wait. They replay byte for byte in the normal executor.

[Configuration](early-entry13.json), [runner](early_entry13.py), and
[report](results/early-entry13/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/early_entry13.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
