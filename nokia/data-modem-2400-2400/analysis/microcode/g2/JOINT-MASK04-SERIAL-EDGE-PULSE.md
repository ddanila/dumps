# A second-bit-edge pulse is too late for the fixed symbol timing

The successful joined transmitter runs offered a chosen D127 phase-step
byte for the first four `127` visits of each data symbol. That models a
phase pulse but supplies the dibit before showing how two serial bits
become available. This [causal candidate](joint_mask04_serial_edge_pulse.py)
starts instead with each selector's unchanged 8031-scrambled eight line
bytes, clocks the 64 bits LSB first at 2,400 bit/s, stores pairs, and
starts a four-visit D127 pulse when the **second** bit of each pair
arrives. With one hypothesized 14.4 MHz oscillator tick per
microinstruction, that pulse occupies 16 microcycles. The earlier A1,
A2 and A3 input fixtures are held fixed. Each call/answer case runs
**1,257,256 real-PROM microinstructions** and captures 838 Y7 samples.

The [DSC board inventory](../board/inventory.json) identifies a
74LS161 and 74LS74 near the 14.4 MHz oscillator, which make a
counter/bit-pair latch a plausible circuit *hypothesis*. Their actual
clocks, clears, serial input pins, D127 mask gates and board nets are
untraced. This test does not infer that Nokia implements the candidate.

The causal second-edge pulses change 85/838 call and 65/838 answer Y7
samples versus the previously verified symbol-start pulse fixture.
Applying the same candidate B5, A2 gate and Q=1 analog path, the
independent reference decoder gives:

| Selector | Errors at previously fixed six-sample alignment | Best errors over eight sample shifts |
| --- | ---: | ---: |
| `40` call | 5/62 | 2/62 (shifts 4 or 5) |
| `60` answer | 3/62 | 2/62 (shifts 4 or 5) |

Thus a pulse launched as soon as the second bit arrives does **not**
reproduce the error-free joined data result under the tested 16-cycle
width, sample clock and analog filter. Merely retiming the receiver by
zero to seven samples does not fix it. The result constrains this
specific causal decoder, not all serial-to-dibit circuits; a buffered
one-symbol pipeline could emit a complete pair at the next symbol
boundary, while other pulse shaping or analog response might change
the outcome. C2 stays open. The [machine report](results/joint-mask04-serial-edge-pulse.json)
records every controller bit pair, D127 pulse event, PROM digest, Y7
hash and eight-offset decision score. Reproduce from the microcode
directory with `python3 g2/joint_mask04_serial_edge_pulse.py`.
