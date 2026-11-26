# A package-budgeted candidate receive phase circuit

The [U15 capacity check](PHOTO-U15-PHASE-GATE-CAPACITY.md) showed that
the photographed SN74S64J cannot by itself compute both observed
mode-conditioned phase bits from the seven candidate state wires and one
assumed mode wire. This experiment makes one complete **logical** route
using photographed packages U13 (six inverters), U15 (one 4-2-3-2 AOI),
U19 (three 3-input NANDs) and U21 (four 2-input NORs). The [TI LS04](https://www.ti.com/lit/ds/symlink/sn74ls04.pdf),
[S64](https://www.ti.com/lit/ds/symlink/sn54s64.pdf),
[LS10](https://www.ti.com/lit/ds/symlink/sn74ls10.pdf) and
[LS02](https://www.ti.com/lit/ds/symlink/sn74ls02.pdf) data sheets specify
those gate functions. The photographed markings are recorded in the
[inventory](../board/inventory.json). None of the proposed signal nets is
identified from a trace.

Let `s0`–`s6` be the candidate U12/U14/U3 capture bits and `m` be the
**assumed** mode bit (`01→0`, `81/A1→1`). The proposed net equations are:

```text
U19a = NAND(s0, s2, s3)
pre  = NOT(U19a)                     [U13]
U15Y = NOT[(~s1 & ~s2 & ~s6 & ~m)   [ABCD]
           + (~s0 & ~s1 & s6)       [GHI]
           + pre                    [EF, second input high]
           + (~s0 & ~s2)]           [JK]
P0   = NOT(U15Y)                     [U13]
U21a = NOR(m, s6)
U21b = NOR(U21a, U21a)              [m OR s6]
P1   = NAND(s2, U21b, HIGH)          [U19b]
```

U13 supplies the four complements `~s0`, `~s1`, `~s2`, `~s6`, plus `pre`
and `P0`: all six inverters. A third U21 NOR, with tied inputs, supplies
`~m`. This uses one U15, two of U19's three NANDs and three of U21's four
NORs. It requires high ties for the spare U15 EF and U19b inputs. Its
logic uses package capacities exactly, but fan-out, timing, tie points,
mode source, capture storage and physical serializer wiring remain assumed.

The [replay](photo_u15_u19_u21_phase_route.py) evaluates this exact
network against all **34 observed phase labels**: 22 in `01` mode and
12 in `81/A1` mode. It then recomputes each phase transition from saved
real-PROM capture states. The six call/answer × level cases at carrier
offset 88 and four changed-mode call/answer cases at offsets 120 and 128
have **0/640 dibit errors** in total. Every captured state in these
runs was already among the 34 labels. Thus the result verifies the
package-budgeted equations and replay, but is not an independent
unseen-state test or evidence of the actual U13/U15/U19/U21 connections.

The [machine report](results/photo-u15-u19-u21-phase-route.json) records
the source run hashes and every case. Reproduce from the microcode
directory with:

```sh
python3 g2/photo_u15_u19_u21_phase_route.py
```

C3 and G2 remain open. Next freeze this exact circuit and run a new
real-PROM carrier/gain fixture that visits previously unseen capture
states. In parallel, constrain the assumed `D3EB` mode and phase-bit
routes to the 8251 with the board photos or a discriminating timing test.
