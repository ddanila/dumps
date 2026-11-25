# A same-net phase candidate carries a 3F7 table byte into a branch

The [3F7 dataflow run](LOWER-I-ROM-DATAFLOW.md) writes ROM-dependent R10 but
leaves it isolated under fixed E4/E2 levels. The
[phase experiment](lower_i_address_phase.py) keeps U2 I6←U11.0 and the real
four-PROM program, then tests when the photo-candidate E4/E2 nets might be
sampled. The existing fixture holds I7/A0=`1` and I0/A1=`0`. A new optional
scenario setting applies explicit, provenance-labelled bit levels at selected
microinstructions, after the global levels. This is a **timing hypothesis**;
neither the latch clock nor the E4/E2 continuation is traced.

Each case runs 512 microinstructions from Q=5 and zero RAM. The A8 comparison
changes the bank only at `3F7`.

| E4/E2 schedule | Upper-bank `3F7` reads | Lower-bank reads | First bank-dependent PC difference |
| --- | ---: | ---: | ---: |
| Fixed `1/0` on I and A | 59 | 59 | none |
| A0/A1=`0/1` at `3F9/3FA`, I unchanged | 4 | 59 | cycle 75 |
| **I7/A0=`0`, I0/A1=`1` together at `3F9/3FA`** | **59** | **10** | **cycle 123** |
| I7/A0=`0`, I0/A1=`1` globally | 0 | 0 | none |

The same-net per-word case respects the proposed coupling of address and
instruction pins. It keeps the upper-bank ROM loop alive. After four startup
reads, selected addresses repeat `11F, 10A, 11E, 119, 117, 105` in this
fixture; ALU Y at `3F8`, `3F9` and `3FA` takes 8, 7 and 8 distinct values,
respectively. The lower-bank alternative exits through `3EE`. These are
internal bytes and branches, not measured carrier samples or DAC input codes.

An isolated-byte control shows a direct causal route. Replaying every
upper-bank `3F7` byte as a PC-keyed D sequence exactly reproduces the real-ROM
trace digest. Replacing **only visit 20** with the lower-bank byte at the same
address (`117`: `44→33`) first changes ALU Y at cycle 208 (`3F9`), then changes
the test at cycle 210 (`3ED`): the original goes to `3EA`, while the changed
run goes to `3EE`. Their PCs first differ at cycle 211, and the changed run
reaches only 21 `3F7` visits in the window. This proves a ROM-byte-to-branch
path **under the stated phase schedule**, not that Nokia clocks those nets
that way.

The [machine report](results/lower-i-address-phase.json) records the four
controls, ROM and ALU sequences, branch witness, trace digests and source
hashes. The DSP controller bitstream is not consumed in this loop and the
output latch route remains untraced. The next test should constrain this phase
against the photographed latch controls and look for a route from these
changing internal bytes to a DAC sample stream.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_address_phase.py
```
