# Controller A3-to-A4 frame edge is a candidate mode event

The [interrupt-paced controller run](MAIN-LOOP-TIMER1-SEGMENT2.md) reaches
34 A3 polling iterations followed by eight A4 iterations for each of the
call (`40`) and answer (`60`) selectors. This probe reconstructs the **held**
four-byte CD4094 frame across iterations without a new send, rather than
examining only frames transmitted during a state. It uses the unchanged 8031
ROM, Timer 1 interrupts, synthetic receive/status events, and the explicitly
held-positive RAM15 gate from that run.

| Selector | A3 held frames | A4 held frame | A3→A4 edge | P1 at edge |
| --- | --- | --- | --- | --- |
| `40` call | `D0 42 81 BA`, `D0 42 A1 BA`, `D0 42 C1 BA` | `D0 42 A1 BA` | `D0 42 81 BA` → `D0 42 A1 BA` | `D8` → `D8` |
| `60` answer | same | same | same | same |

The only byte bit changing at the boundary is bit 5 of the third frame byte.
There is **no single held frame bit or P1 bit** whose value separates every
A3 iteration from every A4 iteration: `D0 42 A1 BA` also occurs during A3,
and P1 is `D8` throughout both intervals. The exact third-byte `81→A1`
transition occurs once in each run, at A4 entry. A rise of third-byte bit 5
alone is insufficient: one also occurs in A2 and another in A3. A decoder
would need frame history or another qualifying input to recognize this
particular edge.

This edge is a **candidate** for a DSC mode-control experiment. It does not
identify a physical connection, a held A4 mode level, or the echo
training/freeze command. A3→A4 is the symbol-training-to-data transition in
this controller fixture; whether the echo canceller trains or freezes there
has not been established. Test any use of this event as a labelled decoder
hypothesis against a control with no event, while keeping ADC and receive
output routes explicit. A resulting change would constrain that fixture,
not pass C4 on its own.

The [machine report](results/controller-a3-a4-mode-edge.json) includes
iteration indices, bit-rise controls, fixture limitations and source hashes.
Reproduce it with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/controller_a3_a4_mode_edge.py
```
