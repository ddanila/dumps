# Literal controller-frame bytes do not explain a sustained A1 tone in the D127 loop

The unchanged 8031 ROM emits `80 02 88 7A` for state A0, `80 02 81 7A`
for A1 and `80 02 88 7A` for A2 in the fixed
[state/frame fixture](STATE-FRAME-CROSSCHECK.md). These are observed
controller bytes; their recipient and meanings are not traced. The
[frame-lane screen](photo_127_controller_frame_steps.py) asks whether any one
held byte could directly feed D127 in the [photo-compatible PC129 loop](PHOTO-I0-HOLD.md).
It also checks simple polarity and serial bit-order alternatives before
comparing with the [fast-clock step candidates](PHOTO-127-FAST-STEP-CANDIDATES.md).

| State | Frame | Exact 1,800/2,100 Hz phase-step matches at divisors 1 or 3 |
| --- | --- | --- |
| A0 | `80 02 88 7A` | Lane 2 literal `88`: 2,100 Hz at divisor 1 |
| A1 | `80 02 81 7A` | None |
| A2 | `80 02 88 7A` | Lane 2 literal `88`: 2,100 Hz at divisor 1 |

Each of the five distinct literal bytes was also supplied as a held D127
input for 3,000 real-PROM microinstructions. `02`, `7A`, `80` and `88`
each sustain 740 PC129 reads, whose phase, ROM operand and ALU recurrence
were checked. `81` reaches only **125** PC129 reads before leaving this loop.
Thus the one byte that distinguishes A1 from A0/A2 does not sustain the
candidate sampled tone path in this fixture. The 640-sample B5 projection
for literal `88` at one oscillator period per microinstruction peaks at
2,100 Hz (target-bin variance fraction 0.486); at three periods its peak is
3,900 Hz. The other sustained literal bytes do not peak at 2,100 Hz under
either integer-ratio gate. No long sample projection is made for `81`
because the executed microcode exits the loop.

This excludes a **direct held frame byte** as an explanation for a sustained
A1 2,100 Hz output under the tested D127 route, mapping and clock model.
The A1 countdown of 2,605 ticks resembles a 2,100 Hz handshake interval,
but its actual signal command has not been established. A CD4094 output may
select a ROM parameter, choose another loop or combine bits before D127;
the frame's physical destination and bit order are untraced. The next useful
test is a photo-compatible control path that selects a changing D127 source
or a different output site in response to the A0/A1/A2 frame change. The
[machine report](results/photo-127-controller-frame-steps.json) records
all lane transforms, executed read counts, spectra, trace digests and source
hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_controller_frame_steps.py
```
