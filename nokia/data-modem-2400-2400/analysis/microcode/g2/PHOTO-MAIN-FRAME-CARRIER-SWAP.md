# A main-loop frame can select a 1,800 Hz candidate phase walk

The [ROM-executed 8031 main-loop streams](MAIN-LOOP-SERIAL.md) have four
representative frame classes. Their second-last byte is `A1` in every class:
`D0 47 A1 22` for selectors `00/20` and `D0 42 A1 BA` for `40/60`.
Under the candidate four-CD4094 cascade, logical chip 1 Q8→D0 therefore
holds `A1`. The [carrier-swap replay](photo_main_frame_carrier_swap.py)
exchanges the candidate D0 and D4 wires before q3 D127, giving `B0` in
all four classes. Among the 28 single pairwise bit swaps, this is the only
one that maps `A1` to an exact ±1,800 Hz phase-step byte for the tested
integer clock ratios. The crossing and CD4094-to-DSP route are **untraced
wiring hypotheses**.

Each class runs 3,000 real-PROM microinstructions cleanly. D127=`B0` stays
in the `127–12A` loop for 740 selected PC129 upper-bank reads; every ROM
address and ALU Y matches the executed phase relation. D12C is never
selected, and the four traces match because the proposed D127 input is the
same. The controller's real USART-01 data bytes have **not** been coupled to
this loop, so this is a command/frame-dependent steady-path check, not a
data modulator.

At a hypothetical 9,600-sample/s gate, one oscillator period per
microinstruction and the **upper** Am27S31 bank, the 640 projected `129` Y
bytes peak at 1,800 Hz with 0.626 of their variance in that bin. A simple
full DAC08 bus hypothesis consistent with the photographed 74LS273 Q4→DAC08
B5 segment—ordered Y→LS273 D, then Q4/Q5 exchanged to DAC B pins—also
peaks at 1,800 Hz, fraction **0.604**. All 16 start-phase alignments are
spectral rotations. This full-code result does **not** require the single
B5 bit itself to peak at 1,800 Hz; it peaks at 4,800 Hz in the same fixture.

| Am27S31 bank | Microinstruction divisor | `129` Y peak | Candidate full DAC-code peak | Full-code 1,800 Hz fraction |
| ---: | ---: | ---: | ---: | ---: |
| lower | 1 | 3,600 Hz | 1,200 Hz | 0.183 |
| lower | 3 | 1,200 Hz | 3,600 Hz | 0.082 |
| upper | 1 | **1,800 Hz** | **1,800 Hz** | **0.604** |
| upper | 3 | 600 Hz | 600 Hz | 0.095 |

The [machine report](results/photo-main-frame-carrier-swap.json) records the
four controller frames, executed trace digests, 16-alignment checks, all
source/DAC/B5 spectra, and source hashes. This is a more specific carrier
candidate than a generic held phase byte: a real controller frame supplies
the raw `A1` and a minimal proposed wire crossing supplies `B0`. The
full-byte signal still has substantial non-target energy, and no physical
DAC clock, analog waveform, dibit phase reversal, 2,100 Hz handshake tone,
or receiver/echo function is established. The next experiment should inject
the same ROM-executed USART dibits through a labelled, line-rate input route
and ask whether they cause four differential phase changes while preserving
this carrier-rate loop.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_main_frame_carrier_swap.py
```
