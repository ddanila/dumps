# The A3→A4 segment-2 sequence survives interrupt-paced controller timing

The [earlier A4 match](CONTROLLER-SEGMENT2-PATTERN.md) forced the firmware's
countdown to expire at every polling boundary. This
[second unchanged-ROM run](main_loop_timer1_segment2.py) starts with the
same single A0-expiry shortcut, then enables Timer 1 with the controller's
`TMOD=15`, `TH1=FC`, `TL1=21` setup and lets its interrupt advance RAM17:16.
The synthetic seven-byte receive frame and port status remain as before.

With the original zero RAM15 seed, the first timer interrupt makes RAM15
negative. The ROM checks that sign at `1024–1029` and clears the state to
`00`; a four-iteration control confirms `A1→00→00→00`. For the paced run,
the fixture therefore **holds RAM15=01 at each `1000` state dispatch**. This
is an explicit, untraced qualification-gate assumption, not a claim about
the board's source for RAM15.

| Selector | A1 passes | A2 passes | A3 passes | A4 passes | First A5 pass | Modeled Timer 1 interrupts, first A3→first A4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `40` / GPC | 3,577 | 84 | 34 | **8** | 1 | 25 |
| `60` / GPA | 3,542 | 84 | 34 | **8** | 1 | 25 |

A3 writes **no port-01 bytes** in either run. A4 writes eight `FF`-source
bytes, followed by one `03`-source byte at A5. The resulting nine output
bytes are **byte-for-byte identical** to the earlier forced-timer fixture
used by the DSC [segment-2 PROM replay](PHOTO-SEGMENT2-STANDARD-CALIBRATION.md).
Starting at the second bit of A4's first byte, the same 64 bits exactly
match the standard GPC or GPA segment-2 pattern. Every port-01 byte in the
paced run independently matches the controller scrambler calculation.

The final P1 latch is `D8` throughout both A3 and A4. The third frame byte
changes among `A1`, `81` and `C1` during A3; A4's recorded frames have `A1`.
Thus this run does not identify a unique P1 change or one stable four-byte
frame that marks the A3→A4 boundary. The **start of port-01 writes** is an
observed distinction. A3 is now a stronger *segment-1 candidate* because
it precedes the exact segment-2 sequence, lasts across 25 modeled timer
interrupts and supplies no scrambled data, but no 180° line reversals have
been demonstrated for A3.

The emulator increments Timer 1 once per instruction tick, without varying
the count by 8031 instruction machine-cycle cost. The interrupt count is
therefore a program-sequence observation, not measured milliseconds or an
exact 32-symbol duration. RAM15 gating, port status, receive timing, the
frame recipient and DAC/line route remain assumptions. The
[machine report](results/main-loop-timer1-segment2.json) records the state
groups, firmware timers, interrupt counts, frames, P1 values, bytes and
source hashes.
