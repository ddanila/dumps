# `FF` sync hunt is counterfactual for the programmed receive mode

The [continuous real-PROM preamble/data trace](RECEIVER-MASK04-PREAMBLE-SERIAL.md)
recovers 62 consecutive `1` bits from the last 31 of 32 reversal-preamble
symbols, then 32 data bits. The first dibit cannot be decoded from a phase
difference because there is no earlier captured symbol. The supplied test
waveform says it is `11`; whether a physical RxD circuit presents those
two bits remains a hypothesis.

The [alignment screen](receiver_mask04_sync_hunt_alignment.py) reads the
four existing real-PROM traces. It starts a **counterfactual internal `FF`
hunt** at a chosen bit, accepts the first eight consecutive `1` bits, and
groups later bits into LSB-first characters. The
[Intel 8251A handbook](https://bitsavers.trailing-edge.com/components/intel/_dataBooks/1979_Intel_Peripheral_Design_Handbook.pdf)
shows that mode bit D6 selects external sync detect. The controller's
executed mode byte `CC` sets D6, so **the programmed receiver does not
internally hunt for `FF`**. It waits for a positive-going signal on SYNDET
pin 16, then starts assembling characters at the next RxC rising edge.
This screen is a framing counterfactual, not a chip-level emulation.

The screen varies 0–7 hypothetical leading `1` bits and eight hunt-start
offsets. Two leading bits reproduce the supplied 32-symbol `11` preamble;
other counts represent truncated observation or earlier fill.

| Counterfactual assumption | Result in each of four traces |
| --- | --- |
| Two leading `1` bits; hunt starts at reconstructed bit 0 | `FF` match after bit 8, seven more whole `FF` characters, then data on a character boundary |
| Same two leading bits; hunt starts at bits 1–7 | Data begins 7–1 bits into a character |
| All 64 leading-bit/hunt-start pairs | Eight align the data; 56 do not |

With the aligned `2,0` assumption, the four data bytes are `50 49 78 F0`
for seed `A431` and `EE C5 F4 18` for `C991`, at both 0° and 45°. The
other seven aligned pairs produce the same bytes under this counterfactual.
These results cannot establish the physical RxC phase or the actual
mode-`CC` byte boundary. The
[machine report](results/receiver-mask04-sync-hunt-alignment.json) records
the boundary offsets and source trace digests.

The [external-SYNDET handoff](RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md)
tests the programmed behavior under explicit pulse timing. Keep C3 open:
the DSC-to-DSU SYNDET, RxD and RxC connections remain untraced, but they
can be tested as labelled hypotheses. Reproduce this counterfactual screen
from the microcode directory with
`python3 g2/receiver_mask04_sync_hunt_alignment.py`.
