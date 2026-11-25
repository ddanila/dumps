# A1 frame bit 5 is a controller counter phase

The isolated A1 send produces third serial byte `81`; the preserved
[main-loop run](MAIN-LOOP-SERIAL.md) produces `A1` in its first two A1
iterations. [Unchanged 8031 ROM execution](a1_counter_phase.py) resolves this
fixture discrepancy: the main loop enters the first A1 output build with
RAM24 bit 5 set. That flag sets RAM32 bit 5 and reloads RAM49 with 10. The
isolated send enters with the flag clear and RAM49 zero, so bit 5 stays clear.

Four representative main-loop selector classes (`00`, `20`, `40`, `60`) give
the same first four output builds. The probe observes RAM immediately before
PC `012F` and after PC `0266`, then checks the outgoing third byte:

| Iteration | State | RAM24 before | RAM32 before→after | RAM49 before→after | Action |
| ---: | --- | --- | --- | --- | --- |
| 0 | A1 | `20` | `00`→`A1` | 0→10 | Reload on changed-input flag |
| 1 | A1 | `02` | `A1`→`A1` | 10→9 | Hold phase; decrement |
| 2 | A2 | `22` | `A1`→`A8` | 9→10 | Reload in new state |
| 3 | A2 | `02` | `A8`→`A8` | 10→9 | Hold phase; decrement |

This explains why the isolated `81` and preserved `A1` values cannot be
compared as if state A1 alone selected the byte. The `A1` value is already
present at the **first** A1 main-loop build because of flag24.5; it is not
evidence of a later tone-to-data state transition.

The same polling-loop fixture was then rerun with its artificial timer
underflow bit cleared at each A1 loop entry. It keeps executing the controller
ROM's receive, output-build and serial-send paths with RAM/SFR state preserved.
All four selector classes stay in A1 for 12 iterations and produce the same
third-byte sequence: `A1` on iterations 0–10, then `81` on iteration 11.
RAM49 counts from 10 to 0 before the last frame, when the ROM-table reload
sets it to 4. This is a sustained-A1 **diagnostic fixture**: interrupts are
disabled, and the harness suppresses the supplied expiry event. It does not
measure the real 2.6-second interval or the analog tone.

To see the full local counter trajectory, a second probe preserves the 8031
RAM/SFR image across 20 directed A1 send calls. Starting from the isolated
zero fixture, all 20 sends emit `81`. Starting after a forced A0→A1 expiry
also emits `81` throughout. In a third fixture, flag24.5 is supplied for the
first call, as observed in the main loop, and cleared before the second call,
as observed between its first two iterations:

| Directed calls | Third serial byte | RAM49 after | Counter action |
| --- | --- | --- | --- |
| 0 | `A1` | 10 | Flag reload |
| 1–10 | `A1` | 9→0 | Held phase countdown |
| 11 | `81` | 4 | Clear bit 5; ROM-table reload |
| 12 | `C1` | 3 | Toggle bit 6 |
| 13–19 | `C1` | 2→0, then held | Final countdown |

The [machine report](results/a1-counter-phase.json) contains 48 forced-expiry
main-loop observations, 48 held-A1 observations, 60 repeated-send
observations, the exact fixtures,
ROM/source hashes, and per-build comparisons against the independently
validated [output32 reference](../../controller/OUTPUT32.md). Every observed
third serial byte equals the builder's RAM32 output; execution and reference
agree on RAM32/49/4A/65 in every case.

The repeated sends and one flag clear are harness-directed. Their call count
is not a measured A1 duration. Both main-loop variants still use synthetic
receive events. No physical CD4094-to-DSC route, DAC clock, or line waveform
follows from these bytes alone. The simple bit-5 tone/data decode in
[the earlier candidate](PHOTO-CONTROLLER-MODE-DECODE.md) would change its
candidate output during A1, from `B0` to `88`, after the eleventh held
iteration. That delayed change may be a useful hypothesis to test, but it is
not yet a demonstrated 2,100 Hz tone. Next replay the changing frame sequence
through candidate DSC input and DAC routes, and establish the A1 duration
with controller timer events rather than the held-state fixture.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/a1_counter_phase.py
```
