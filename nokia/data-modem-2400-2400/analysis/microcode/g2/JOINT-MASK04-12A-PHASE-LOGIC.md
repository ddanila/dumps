# A four-phase rule behind the six-bit receive transitions

The [six-bit receive rule](JOINT-MASK04-12A-FROZEN-FIFTH-CHALLENGE.md)
uses a 91-entry table keyed by consecutive six-bit `3F8` Y states. A
DPSK receiver should instead recover a phase for each state and decode
the *difference* between consecutive phases. I tested that stricter
structure on the same 14 labelled development cases: 896 real-PROM
receiver transitions, 18 observed states and all 24 assignments of
dibit values to quarter-turn steps.

Exactly two mirror-image conventions satisfy every development edge:
dibits `0,1,2,3` represent phase steps `2,1,3,0`, or `2,3,1,0`.
The 18 states form one connected graph, so a phase is fixed for each
state up to a common rotation. With the first convention frozen, all
12 untouched third-payload cases at phase offsets 32 and 96, across
75%, 100% and 125% gain, decode **64/64 dibits exactly**. Their decoded
sequences match the earlier 91-key decoder byte for byte. No
holdout label is used to choose a phase or convention.

The 18 observed phases also admit a two-output combinational decoder
with three product terms per output, minimizing each output separately
by term count and then literal count. Let `s0…s5` be first-capture
`Y5,Y6,Y7`, then second-capture `Y7,Y4,Y6`. One such cover is:

```text
p0 = (!s2 & s3 & !s4) | (s1 & !s3 & s5) | (s0 & s2 & s3 & !s5)
p1 = (s3 & s5) | (!s0 & s3) | (s0 & !s2)
phase = p0 + 2*p1
dibit = inverse_convention((phase_now - phase_previous) mod 4)
```

This is a **candidate logic function**, not an identified Nokia
circuit. The minimization treats the other 46 possible six-bit states
as don't-cares. It is therefore exact on the observed development and
both third-payload phase starts, but its outputs on unseen states are
unvalidated. It also fails the [one-visit-late clock](JOINT-MASK04-12A-SIXTH-LATE-CAPTURE.md):
19/64 call and 21/64 answer dibits are wrong at nominal gain. That
failure strengthens the requirement to constrain the physical capture
edge; it does not change the original 46/93 result.

The [phase graph report](results/joint-mask04-12a-phase-potential.json)
and [Boolean cover report](results/joint-mask04-12a-phase-boolean.json)
include the exact state phases, all holdout decisions, source hashes
and limitations. Reproduce with:

```sh
python3 g2/joint_mask04_12a_phase_potential.py
python3 g2/joint_mask04_12a_phase_boolean.py
```

This replaces a key-by-key empirical interpretation with a
phase-difference interpretation of the executed receive loop, but
does not establish the external latches, ADC timing or decision
logic. C3/G2 remain open. Next test a fresh payload or carrier/timing
condition that produces unseen states, and compare this frozen
Boolean circuit with photo-compatible latch/gate routes.
