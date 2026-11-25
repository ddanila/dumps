# No simple dibit decision in the joint map's D3F8 state bytes

The [joint TX/ADC map](JOINT-UPPER-SOURCE.md) executes the full candidate
transmit stream and retains ADC high-nibble information. That does not yet
show demodulation. The [direct-bit screen](joint_upper_receive_bit_screen.py)
and [small-codebook screen](joint_upper_receive_codebook.py) therefore run
the *same fixed map* on real-PROM receive traces and test whether recurring
state exposes a dibit decision.

Seven reference streams are used: three periodic and four seeded
nonperiodic 16-dibit middles. An independent reference receiver recovers
each stimulus. Every DSC run selects 24,000 held complementary ADC bytes
at `D3F8`, where the modeled upper instruction is `D5`. The screens
capture Y at `3F8–3FA`, Q and all 16 RAM bytes after each `3FA` visit.
Training uses two periodic streams and one nonperiodic stream, 36 checked
dibits at symbols 2–13. A third periodic stream and three nonperiodic
streams supply 48 holdout checks. Symbol lags −2…+2 and all 1,500 fixed
visit phases are tested.

The direct-bit screen tries each bit of the 20 state channels with either
polarity. The fewest training errors are **2/36** for each target dibit
bit; no candidate fits training exactly. Its lowest combined-error
candidate still makes 14/48 and 18/48 holdout errors for the two bits.

The codebook screen learns a deterministic byte-to-dibit lookup from a
current channel byte, its XOR with the previous symbol's byte, or their
modulo-256 difference. It allows at most 4, 8 or 16 code values. No
tested codebook fits training exactly. Even with 16 values, the best
candidate with at most four training errors makes **27/48**, **37/48** or
**42/48** holdout errors for those three operations. The
[bit report](results/joint-upper-receive-bit-screen.json) and
[codebook report](results/joint-upper-receive-codebook.json) retain the
candidate fields, counts, trace digests and source hashes.

This excludes only these single-channel, fixed-phase readouts under the
declared ADC and instruction hypotheses. It does not rule out a
multi-sample filter, a two-channel code, a different decision site or a
separately clocked output latch. No internal state bit has been tied to
USART RxD, and echo cancellation remains unshown. The next useful test
should use the operations and timing of the reached microinstructions to
propose a small multi-sample readout, then validate it on independent
streams and a candidate output route. The [sampled-state DPSK screen](JOINT-UPPER-SAMPLED-STATE-DPSK.md)
now tries one such readout family: center-sampled `Y3F8` retains a distorted
waveform but does not give reliable holdout decisions.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_receive_bit_screen.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_receive_codebook.py
```
