# Held USART bits change the phase, but also change the carrier rate

The [main-frame carrier candidate](PHOTO-MAIN-FRAME-CARRIER-SWAP.md) holds
D127=`B0` after a hypothetical CD4094 D0/D4 crossing. The
[line-rate replay](photo_main_frame_line_hold.py) keeps that frame input and
adds a simple controller-data route: each real 8031 USART-01 bit, LSB first,
clears either D127 D4 or D5 throughout its full bit time when the bit is one.
The 14.4 MHz oscillator with one period per microinstruction gives 1,500
visits to the four-word `127–12A` loop per 2,400-bit/s line bit. The wire,
gate, timing and DAC path are **hypotheses**, not observed connections.

For each of the four ROM-executed main-loop stream classes and both D lanes,
13,000 real-PROM microinstructions execute cleanly. The first two full bit
holds and start of the third are reached. Every selected D127 byte, PC129
ROM address and ALU Y matches the cumulative phase recurrence, with no
second-loop entry. A candidate DAC08 code is captured every 375th PC129
visit from Y through the minimal photo-B5-compatible Q4/Q5 bus swap. The
report records its first nine executed codes per case.

| Controller class | First three line bits | D4-clear phase difference after bits 1 / 2 | D5-clear difference |
| --- | --- | --- | --- |
| `00` | `0 1 1` | `0 / 64` | `0 / 128` |
| `20` | `1 1 1` | `64 / 128` | `128 / 0` |
| `40` | `1 0 0` | `64 / 64` | `128 / 128` |
| `60` | `0 0 0` | `0 / 0` | `0 / 0` |

Those differences are real internal state effects **under this D-input
route**: each held D4 clear adds 64 to the phase relative to the baseline
after one bit, and each D5 clear adds 128. But the phase increment is also
different at every visit *during* that bit. A 640-sample projection of the
proposed 9,600-sample/s full DAC code peaks at **1,800 Hz** with a held zero
(D127=`B0`), **3,600 Hz** with
a held D4-clearing one (D127=`A0`), and **600 Hz** with a held D5-clearing one
(D127=`90`). Thus this direct held-bit gate creates a frequency excursion,
not an isolated differential phase step on a steady 1,800 Hz carrier.

The [machine report](results/photo-main-frame-line-hold.json) records the
eight traces, bit-boundary phases, candidate DAC codes, held-level spectra
and source hashes. The result does not exclude a short symbol-boundary
pulse, a decoded dibit gate, another loop, or analog pulse shaping. A next
test should derive any such gate from photo-compatible hardware timing rather
than insert the desired phase steps by hand; the real USART bits and DAC
clock must remain explicit in the scenario. No receiver or echo-canceller
behavior is shown here.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_main_frame_line_hold.py
```
