# `FF` sync hunt gives a conditional, not unique, receive-byte boundary

The [continuous real-PROM preamble/data trace](RECEIVER-MASK04-PREAMBLE-SERIAL.md)
recovers 62 consecutive `1` bits from the last 31 of 32 reversal-preamble
symbols, then 32 data bits. The first dibit cannot be decoded from a phase
difference because there is no earlier captured symbol. The supplied test
waveform says it is `11`, but whether a physical RxD circuit would present
those two bits to the USART is still a hypothesis.

The [alignment screen](receiver_mask04_sync_hunt_alignment.py) reads the four
existing real-PROM traces; it does not rerun or modify them. Its simplified
external 8251A model starts hunt at a chosen bit, accepts the first eight
consecutive `1` bits as `FF`, and groups subsequent bits into LSB-first
eight-bit characters. The [Intel 8251A handbook](https://bitsavers.trailing-edge.com/components/intel/_dataBooks/1979_Intel_Peripheral_Design_Handbook.pdf)
describes synchronous receive sampling and sync-character hunt; this screen
is a boundary model, not a chip-level emulation or observed USART event.
It sweeps 0–7 hypothetical leading `1` bits and eight hunt-start offsets.
Two leading bits reproduce the supplied 32-symbol `11` preamble; other
counts represent a truncated observation or earlier fill.

| Assumption | Result in each of four traces |
| --- | --- |
| Two leading `1` bits; hunt starts at reconstructed bit 0 | `FF` match after bit 8, seven more whole `FF` characters, then data on a character boundary |
| Same two leading bits; hunt starts at bits 1–7 | Data begins 7–1 bits into a character |
| All 64 tested leading-bit/hunt-start pairs | Eight align the data; 56 do not |

With the aligned `2,0` assumption, the four data bytes are `50 49 78 F0`
for seed `A431` and `EE C5 F4 18` for `C991`, at both 0° and 45°. The
other seven aligned pairs produce the same bytes: repeated `FF` fill can
provide a sync match at several entry phases. Thus `FF` acquisition alone
does not identify the missing first symbol, RxC phase or the actual first
data-byte boundary. The [machine report](results/receiver-mask04-sync-hunt-alignment.json)
records all boundary offsets, trace digests and source hashes.

Keep C3 open and G2 active. The next bounded test should assume a
photo-compatible RxD and RxC route, vary the hunt-entry/clock phase and
check whether an executed receive event or controller read distinguishes
the eight aligned cases. The DSC-to-DSU connection remains untraced; its
absence is not a goal blocker. Reproduce this screen from the microcode
directory with `python3 g2/receiver_mask04_sync_hunt_alignment.py`.
