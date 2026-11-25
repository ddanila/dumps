# A two-wire permutation makes the A1 frame select a 2,100 Hz candidate loop

The [executed 8031 state replay](CONTROLLER-STATE-PIN-CHANNELS.md) sends
`80 02 88 7A` in A0/A2 and `80 02 81 7A` in A1. Under the candidate
four-CD4094 cascade, logical chip 1 Q8→D0 presents `88` versus `81`.
The [bit-swap runner](photo_cd4094_bit_swap_tone.py) tests a simple alternative
to the direct bus route: exchange the candidate D0 and D3 wires before the
DSC2847's D127 input. This is a **wiring hypothesis**, not a visible trace.
It turns A1 `81→88` and A0/A2 `88→81`; chip 0's held `7A` supplies D12C.
The q3 field mapping, held-I0 circuit and upper ROM bank remain assumptions.
Among all 28 single pairwise bit swaps of the candidate byte, D0/D3 is the
only one that maps A1 to any exact 2,100 Hz phase-step byte for the tested
integer-ratio output gate. This narrows the simple permutation hypothesis;
it does not provide evidence that the actual board crosses those wires.

| Controller state | P1.5 | Candidate D127 | PC129 reads | PC12E reads |
| --- | ---: | ---: | ---: | ---: |
| A0 | 1 | `81` | 125 | 613 |
| A1 | 0 | `88` | 740 | 0 |
| A2 | 0 | `81` | 125 | 613 |

All three 3,000-microinstruction real-PROM runs are clean, and every selected
ROM address and first-loop ALU Y matches the phase recurrence. At a hypothetical
9,600 samples/s output gate and **one oscillator period per microinstruction**,
the executed A1 recurrence projects a 640-sample Y-byte stream with a
2,100 Hz peak and target-bin variance fraction **0.345587**. The separate
photo-candidate Y7→74LS273 D4→Q4→DAC08 B5 bit has the same peak with fraction
**0.485502**. All 32 start-phase alignments are spectral rotations. At three
oscillator periods per microinstruction, both peak at 3,900 Hz instead. The
full Y series has 30 distinct codes but a substantial non-target component;
its peak is not a demonstrated sine-wave DAC output.

The same run screens every raw U10/U11/U17/U18 PROM data-bit edge. Eleven
bit/edge choices rise or fall at every A1 PC129 read. **All eleven also fire
at every A0 PC12E read**, so none is an A1-only direct latch clock. A decoded
PC129-qualified or externally controlled clock would be needed to keep the
two paths separate. No tested run reaches candidate output words `392` or
`39E`; the 74LS273 full data bus and clock remain untraced. A2 shares A0's
frame and loop despite its different P1.5 level, so P1.5 may still matter to
the real output circuit.

This is a concrete candidate linking a controller state to a sustained ROM
phase walk and the proposed tone frequency, **conditional on the D0/D3 wire
swap and divided output gate**. It does not yet show dibit phase reversals,
1,800 Hz carrier output, a physical DAC waveform, or receiver/echo behavior.
The [machine report](results/photo-cd4094-bit-swap-tone.json) records the
three traces, spectral checks, PROM-edge screen and source hashes. Next test
whether a photo-compatible latch/mux can implement the bit permutation and
qualify PC129 captures; if it cannot, drop this route and continue with other
input and output hypotheses.
The [joint state/data check](PHOTO-STATE-DATA-BUS-COMPATIBILITY.md) shows
that this D0/D3 crossing and the later D0/D4 carrier crossing cannot be one
fixed chip-1 byte wiring under the tested phase-step model.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_cd4094_bit_swap_tone.py
```
