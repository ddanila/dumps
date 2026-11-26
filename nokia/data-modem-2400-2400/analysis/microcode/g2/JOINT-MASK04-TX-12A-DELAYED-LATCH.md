# The `12A→127` clock works only if it captures the preceding `12A` Y

The [two-bit PROM gate](JOINT-MASK04-TX-12A-GATE.md) is high at `12A`
and falls when the next `127` word is fetched in the tested transmitter
mode. This [full-stream replay](joint_mask04_tx_12a_delayed_latch.py)
models a counter selecting every 375th NAND rising edge and two explicit
relative propagation orders:

- **Early gate:** the clock arrives before the new `127` ALU Y settles,
  so the assumed 74LS273 captures the preceding `12A` Y byte.
- **Late gate:** the new `127` ALU Y settles first, so the latch captures
  `127` Y instead.

Four controller-fed executions—call and answer, with the selected
Am27S31 bank upper and lower—each run **1,248,256 real-PROM words**.
Their trace digests match the earlier bank-phase and gate replays. Each
timing order produces 832 candidate DAC sample bytes. With the six
surviving photo-compatible bus orders and the previously assumed A2
mute/analog filter, the comparison is:

| Selector | Timing | Samples changed by ROM-bank switch | A1 tone peak on all six buses | A3/A4 errors across six buses, either bank |
| --- | --- | ---: | ---: | --- |
| Call `40` | Early, capture `12A` | 198/832, bit 0 only | 2,100 Hz | `0 0 0 0 0 0` |
| Call `40` | Late, capture `127` | 0/832 | 2,100 Hz | `1 0 1 0 0 0` |
| Answer `60` | Early, capture `12A` | 202/832, bit 0 only | 2,100 Hz | `0 0 0 0 0 0` |
| Answer `60` | Late, capture `127` | 0/832 | 2,100 Hz | `3 2 3 2 2 2` |

The counter-qualified early edge reproduces the prior settled-`12A`
bank contrast, now tied to a specific raw-PROM decode and a named
gate-versus-ALU timing order. A late edge erases that bank contrast and
also worsens the modeled data decisions. The test does not measure
propagation delays; it identifies which ordering the proposed route
requires. The counter, PROM-to-gate/LS273 clock, Y-bus wiring, six DAC
orders, A2 mute and analog output remain assumptions. C2 therefore stays
open. A next discriminator is a photo-compatible gate/data timing
constraint or output waveform measurement against the predicted
16-count DAC-code differences on 198/202 selected samples.

The [machine report](results/joint-mask04-tx-12a-delayed-latch.json)
contains all paired trace hashes, 832-byte hashes, per-bus code hashes,
tone peaks and data scores. Reproduce from the microcode directory with
`python3 g2/joint_mask04_tx_12a_delayed_latch.py`.
