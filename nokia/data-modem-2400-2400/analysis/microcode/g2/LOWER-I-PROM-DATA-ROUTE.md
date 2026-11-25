# Read-valid PROM data sources carry a 3F7 byte into the branch

The [per-word E4/E2 phase screen](LOWER-I-ADDRESS-PHASE.md) exposed a
ROM-to-branch route, but its changing enable levels would disable U10/U11
data in the same phase. The [PROM-data source screen](lower_i_prom_data_route.py)
instead keeps **U10 E2 low and U11 E4 high** as valid-read assumptions, and
lets two paired Am2901 nets take candidate PROM data bits. It keeps the
photo-suggested Q0 fan-outs I7/A0 and I0/A1, but the data-bit-to-latch
connections and any inverter are **untraced alternatives** to the visible
enable-side segments. The emulator does not yet model their capture clock.

The raw PROM pattern at the reached `3ED–3FA` loop is `00000011` for U10 D6
and U11 D2: those bits are low at the first six loop words and high at
`3F9/3FA`. Their inverted forms supply the complementary I7/A0 pattern.
The screen tries the four direct pairs with lower I6←U11.0, Q=5, zero RAM
and 512 real-PROM microinstructions per bank. A8 changes only at `3F7`.

| I7/A0 source | I0/A1 source | Upper-bank selected `3F7` reads | Lower-bank reads |
| --- | --- | ---: | ---: |
| inverted U11 D2 | U11 D2 | 6 | 12 |
| inverted U11 D2 | U10 D6 | 0 | 0 |
| **inverted U10 D6** | **U11 D2** | **59** | **8** |
| inverted U10 D6 | U10 D6 | 0 | 0 |

The surviving pair reaches `3F9` with lower A=`10` and instruction=`21`,
so the earlier `3F7` R10 write can affect arithmetic. In the upper-bank run,
ALU Y at each of `3F8`, `3F9` and `3FA` takes six distinct post-startup
values. The lower-bank run exits through `3EE`; its PC first differs from
the upper-bank run at cycle 107. These are internal modeled values, not DAC
samples.

An isolated-byte control establishes causality. Replaying every selected
upper-bank `3F7` byte reproduces the original full trace digest. Replacing
only visit 30 at ROM address `117` with its lower-bank byte (`44→33`) first
changes ALU Y at cycle 288 (`3F9`). At cycle 306, `3ED` goes to `3EE`
instead of `3EA`; the PCs first differ at cycle 307, and the changed run
reaches 33 rather than 59 `3F7` visits. Thus a real-PROM byte influences
later arithmetic and a branch **under this untraced data-bit source mapping**.

The [machine report](results/lower-i-prom-data-route.json) contains all four
source pairs, bank comparisons, the byte-replay witness, trace digests and
source hashes. This strengthens the algorithmic lead without establishing
the physical latch wiring, a controller-bit input, a DAC-bound sample, or a
line carrier. The next discriminator is a photo-compatible latch capture
and output route for the surviving pair.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_prom_data_route.py
```
