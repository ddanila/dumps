# Sample-paced external RAM changes the four-row trace but not the tested late echo proxy

The [earlier external-RAM screen](JOINT-UPPER-RAM-SAMPLE-CLOCK-ECHO.md)
used the two-row mask-`08` receive fixture. This
[four-row run](joint_mask04_external_ram_echo_screen.py) uses the same
joint mask-`04` field mapping that supported the complete Tx→Rx
handoff. It models a 256×8 external RAM, a sample-paced address
counter, writes at `3EC` during 128 training samples, freezes writes,
and reads the RAM's low nibble into the `3FA` D input from an address
three samples behind. The 9,600 Hz sample hypothesis corresponds to
47/46 four-row receive visits per PCM sample, so the counter advances
once per 47/46 visits. Each case executes **288,047 real-PROM words**
and accepts 9,000 ADC visits.

The stimulus controls are zero, an independent remote DPSK waveform,
the own call-side Y7 candidate output delayed three PCM samples and
halved, and their remote-plus-echo mixture. The own waveform is
reconstructed from the phase recurrence and hash-checked against the
838-sample executed transmitter run. All four controls have a common
64-sample zero tail. For each stimulus, the screen runs both a
write/freeze control without readback and the feedback route.

The first candidate latches `3FA` Y's low nibble. **Every trained RAM
byte remains its initial `01`** for all four inputs, so its readback
changes neither the trace nor `Y3FA`. A neighboring `3F9`-Y low-nibble
latch is active: its frozen RAM has 128 noninitial addresses for zero,
84 for own echo, 88 for remote and 92 for their mixture. Its first
noninitial read changes the real-PROM trace without leaving the
four-row loop. Thus the assumed memory *can* carry input history
through this declared route, although the zero case shows that stored
changes are not echo-specific.

The table compares unsigned `Y3FA` code-space differences between
remote-plus-echo and remote-only inputs. It is a diagnostic output
proxy, **not** a measured analog residual.

| Route | First 32 training samples | Last 32 training samples | Common zero tail |
| --- | ---: | ---: | ---: |
| `3F9` latch, write/freeze only | 0.251 | 0.439 | 0 |
| `3F9` latch, readback −3 samples | 5.172 | 0.439 | 0 |

The `3F9` feedback perturbs the early code stream, but by the last
training window its mixed-minus-remote response matches the no-feedback
control rather than falling. The remote-minus-zero response also
matches that control in the late window (0.313 in both). All eight
`3F9` cases remain in the receive loop and write 6,000 times before
freeze. The feedback trace differs from its same-input control, but
`Y3FA` has no changed visits in the common zero tail. This excludes a
sustained, selective `Y3FA` residual under the tested latch, return,
clock and training duration; it does not exclude a different tap store,
output latch, mode gate or analog residual.

The RAM pins, address counter/mux, low-nibble return, D0 forcing,
write gate, train/freeze signal and DAC/ADC paths are untraced
hypotheses. C4 stays open. The next useful route test should compare
a distinct output site or mode-qualified return against the same
own/remote/mixed controls, rather than interpreting stored RAM bytes
as cancellation. The [machine report](results/joint-mask04-external-ram-echo-screen.json)
contains all trace and memory hashes, loop counts, first changed reads
and early/late code-space comparisons. Reproduce with
`python3 g2/joint_mask04_external_ram_echo_screen.py` from the microcode
directory.

## Other executed outputs and an earlier RAM return

The expanded replay scores the same four stimuli at all three visited
outputs, `Y3F8`, `Y3F9` and `Y3FA`. With the `3F9` latch and `3FA` low-nibble
return, the feedback route leaves the first two output streams identical
to the no-feedback control. At `Y3FA` it changes the early response but
matches the control in the last 32 training samples and common zero tail:

| Output | Late mixed-minus-remote, no feedback | Late mixed-minus-remote, `3FA` return | Late remote-minus-zero, both |
| --- | ---: | ---: | ---: |
| `Y3F8` | 22.027 | 22.027 | 17.504 |
| `Y3F9` | 19.318 | 19.318 | 9.003 |
| `Y3FA` | 0.439 | 0.439 | 0.313 |

A second photo-compatible hypothesis returns the same frozen RAM low
nibble at earlier `3EB` instead. All four cases complete 9,000 ADC visits,
with no receive-loop exit, and the RAM holds 128/84/88/92 changed addresses
after zero/own/remote/mixed training. The first changed read is real within
the fixture: for zero and own echo, address 1 supplies `09` at cycle 1,172.
Yet each complete PROM trace digest is **identical** to its no-feedback
control; all three Y streams and the late code-space comparisons match.
A short differential trace confirms that at cycle 1,172 the `3EB` external
read is marked selected by the ALU, but changing D from `01` to `09` leaves
ALU F=`00` and Y=`F2` in both runs. The selected low-nibble value is thus
ineffective under this mapping and state at that point; the full-run digest
shows no later effect in the tested fixture.

Neither return produces a selective, sustained echo residual at these
executed byte sites. This does not rule out a high-nibble or differently
timed route, another output latch, or a mode-qualified training circuit.
Keep C4 open and test one of those alternatives with the same controls.
