# Fresh 8031 data bytes modulate the executed DSC transmit candidate

The earlier [raw-MSB phase replay](JOINT-MASK04-MSB-DATA-PHASE.md)
used the controller's fixed A4 training pattern. This
[challenge](joint_mask04_fresh_controller_payload.py) executes the
preserved 8031 scrambler routine on nine fresh nonzero plaintext bytes
for each call/answer selector, checking every output byte and 23-bit
history against the independent bit-serial transform. It pairs 64
transmitted bits into 32 dibits after the same one-bit alignment used
at the observed A4 boundary. These data symbols replace A4 in the
joint mask-`04` DSC scenario; the existing 32-symbol tone and
32-symbol segment-1 inputs remain as explicit scenario assumptions.

For each selector, the real four-PROM microprogram executes once with
the new data and once with 32 zero-data dibits. An isolated emulator
instrument captures Y at `127–12A` on the established one-per-1,500-
microinstruction sample schedule. All four capture sites have exactly
the same candidate DAC MSB sequence. Each run executes 1,248,256
microinstructions cleanly.

| Selector | Fresh data MSB samples differing from zero control (of 256) | Direct phase errors (of 32) | Opposite-sign phase errors | Zero control scored against fresh data | Filtered reference errors (of 32) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Call `40`, d=18 | 157 | 0 | 16 | 25 | 0 |
| Answer `60`, d=5 | 110 | 0 | 14 | 20 | 0 |

The raw MSB also retains the assumed A1 2,100 Hz tone phase and all 31
A3 half-turns. Under the same *external* 1,950 Hz bandpass/reference
receiver used in earlier work, the tone peak is 2,100 Hz and both data
streams decode without error. The direct data phasor's worst error is
40.29° against a 45° quadrant boundary, so this raw-bit decision has a
small margin; the filtered result depends on the assumed analog
response.

This is stronger evidence that the candidate `127–12A` routine responds
to **new controller-scrambled data**, rather than merely replaying the
fixed A4 pattern. It remains conditional: the fresh bytes were executed
by the 8031 routine locally, not transmitted by an uninterrupted main
loop; their bits were projected onto the assumed D127 parity/phase
input and one-bit alignment. The Y7→latch→DAC08 B1 route, sample
divider and analog line output are not traced or independently
constrained. C2 therefore remains open. A photo-compatible output
route or independent analog constraint is still needed; lack of a new
continuity measurement does not stop other runnable tests.

The [machine report](results/joint-mask04-fresh-controller-payload.json)
records plaintext and ROM-scrambled bytes, PROM digests, MSB hashes,
phase/control results and source hashes. Reproduce with
`python3 g2/joint_mask04_fresh_controller_payload.py` from the
microcode directory.
