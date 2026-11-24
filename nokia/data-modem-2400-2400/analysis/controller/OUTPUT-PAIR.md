# First and second outgoing bytes preserve event-qualified flags

Controller code 0266–0430 rebuilds outgoing RAM 30 and 31. It preserves exactly
RAM 30.2 and 31.4 from the previous bytes while assigning their other bits from
state byte 34, received inputs, and decoded flags. These are the two bits set
by the [event qualifier](EVENT.md), so their preservation through
this part of the output builder is now tested directly.

The second byte partly mirrors the newly computed first byte. It is not an
independent copy of the received frame. The physical destinations of these
bits remain unknown.

## Reference and input notation

[The reference function](../controller_output.py), `output01`, expresses all
assignments without executing 8051 instructions. It uses S for RAM 34, A–F for
received RAM 2A–2F, and flags from RAM 22–24. In the tables below, `23.4`, for
example, means internal-RAM bit 23.4, not a physical pin.

Define G as true for states 96, B6, B7, C0, or states satisfying
`(S AND E8) == E0` except E0, E4, F0 and F4. The builder stores G in PSW.5,
then uses it while forming the second byte.

## RAM 30

| Bit | Assignment |
| --- | --- |
| 7 | Selector using 22.4, 22.3, F3/F4, B6, C6, and 23.4; rules below |
| 6 | Set if S has bit 7 set and either bit 6 set or `(S AND 1F) >= 3` |
| 5 | State-dependent constant or received A2; rules below |
| 4 | Forced clear if new bit 6 is clear; otherwise selected from A2, B7, or constant one |
| 3 | State-dependent selection from received A2/B7 or a constant, using G |
| 2 | Preserve prior RAM 30.2 |
| 1 | For S=E0–FF, set when `(S AND 0F) >= 3`; otherwise copy 23.4 |
| 0 | Copy received D7 |

Bit 7 is one whenever 22.4 is set. Otherwise, if 22.3 is clear it is the
inverse of F0. With 22.3 set, F3/F4 select: C6 for 00; zero for 01; B6 OR 23.4
for 10; and one for 11 (F3 written first).

Bit 5 is one for states 93, 95, 96, B5, B6, or `(S AND F8) == E0`. Otherwise
it copies A2 for `(S AND FC) == C0` or `(S AND E8) == E8`, and is zero for the
remaining states.

Before its bit-6 gate, bit 4 copies A2 for S=C1 or `(S AND E8) == E8`.
Otherwise it is one if 24.6 is set or received E0 is clear, and copies B7 in
the remaining case.

When G is true, bit 3 is one if E0 is clear, otherwise B7. When G is false,
it copies A2 for S=C1 or `(S AND E8) == E8`, is one for C2/C3/E4, and is zero
otherwise. The full reference preserves the priority of these tests.

## RAM 31

Bits 7, 6, and 5 are forced to zero if 23.7 or 24.6 is set, or if
`(S AND E8) == E8`. Otherwise they copy G, new RAM 30.6, and new RAM 30.5,
respectively.

| Bit | Assignment |
| --- | --- |
| 4 | Preserve prior RAM 31.4 |
| 3 | Copy new RAM 30.1 |
| 2 | Mode/state-gated 23.3; rules below |
| 1 | Copy 22.4 only when S is nonzero, 22.3 is set, and 23.5 is clear; otherwise zero |
| 0 | Inverse of new RAM 31.2 |

Bit 2 is forced clear for S=80–BF with `(S AND 1F) < 9`. Otherwise it copies
23.3, except that when 23.5 is clear and received E3 and E6 are both set, it
uses `23.3 AND 24.3`.

The independently tested serial-output routine applies masks 00 and 03 to
these first two bytes. Thus RAM 30 is sent unchanged, and RAM 31's lowest two
bits are inverted. This does not identify their electrical functions.

## Verification and boundary

[Configuration](../controller-output-pair-scenario.json) selects local entry
0266 and stop 0433, immediately after both writes. R3 is seeded with S, as
established by the preceding builder at 006E. Register bank zero and disabled
interrupts remain explicit local assumptions.

For each of all 256 states, the suite supplies 128 seeded random combinations
of all six flag bytes, all six received bytes, and both prior output bytes,
plus all-zero and all-one cases. Another 2,048 cases sweep prior output bytes
at eight representative states. All 35,328 executions agree on all 128
internal-RAM bytes, PSW.5, stop PC, and stack pointer, without emulator errors.
Every one of the 201 instructions in the section is visited. This is not an
exhaustive sweep of the combined flag/input space.

The local stop matters: later code at 0465 can OR FE into RAM 30 when received
C0 is set. That can force bit 2 high after the preservation demonstrated here.
Other later controller actions and the remaining RAM 32 builder are outside
this experiment. It does not assert that the retained event bits always reach
physical pins unchanged.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_output_pair_study.py
```

[Report](../results/controller-output-pair-study/report.json) contains source
and ROM hashes, fixture/execution digests, coverage, and 48 complete witnesses.
The existing [fourth-byte builder](OUTPUT.md) remains separately
verified. Neither this reference nor the other controller references replaces
unchanged-ROM execution in the harness.
