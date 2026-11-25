# Continuous preamble/data receive replay yields a candidate 2,400-bit/s stream

The [continuous replay](receiver_mask04_protocol_preamble.py) feeds a
32-symbol `11` reversal preamble followed by 16 random data symbols into
the same assumed complementary ADC route, without restarting the DSC
between preamble and data. The preamble is motivated by the
[executed 8251A sync-fill source](USART-SYNC-FILL-SEGMENT1.md); it is a
reference waveform, not a measured remote line signal. Two independent
random streams (`A431`, `C991`) are each run at 0° and 45° carrier phase.
Every case executes **576,047 real-PROM microinstructions**, selects
18,000 ADC bytes at `3F8`, visits `3ED` 72,000 times and completes cleanly.
The proposed four-literal PROM clock gives 18,000 `3F8→3F9` capture edges
and one `18C→3EA` startup edge in every run. Its captured byte sequence
equals the executed `3F8` Y stream.

| Rotation and frozen readout | `A431` data | `C991` data |
| --- | ---: | ---: |
| 0°, nominal Boolean row-pair rule | **0/16 errors**, full coverage | **0/16**, full coverage |
| 45°, row-pair plus `3F8` Y7 rule | **0/16**, full coverage | **0/16**, full coverage |
| 45°, nominal rule control | 10/16 errors | 10/16 errors |
| 0°, diagonal rule control | 15/16 unknown | 14/16 unknown |

Both selected readouts also recover all **31 measurable preamble dibits**
as `11` in every run. The first preamble symbol has no preceding captured
phase, so it is not assigned a differential decision. For data, the check
includes the first symbol immediately after the preamble and the last
symbol in the window; it is broader than the earlier 12-interior-symbol
screens. These are still external readout rules, not executed DSC
instructions or verified output gates.

The [serial timing replay](receiver_mask04_serial_candidate.py) takes the
executed row-3 `3ED` event as a hypothetical decision-available time.
Those events are exactly **12,000 microcycles apart** across the 48-symbol
window. Row-0 `3ED`, `3F8` Y and row-3 `3ED` occur at offsets 0, +13 and
+24 microcycles. A labelled candidate launches the low dibit bit one
cycle after row-3 `3ED`, the high bit 6,000 cycles later, and samples each
at a hypothetical RxC rising edge 3,000 cycles into its bit cell.
All 94 recovered bits (62 preamble ones plus 32 data bits) have 6,000-cycle
spacing and 2,999-cycle setup / 3,001-cycle hold in this discrete timing
model. **If** one microcycle equals one tick of the photographed
14.400 MHz oscillator, this is 1,200 symbols/s and 2,400 bits/s; the
oscillator-to-microcycle and receive-clock divider connections are untraced.

The [Intel 8251A handbook](https://bitsavers.trailing-edge.com/components/intel/_dataBooks/1979_Intel_Peripheral_Design_Handbook.pdf)
identifies RxD as pin 3 and RxC as pin 25 and specifies sampling RxD on
RxC's rising edge in synchronous mode. The
[DSU 3556 front photo](../../../photos/PXL_20261123_114723348.jpg)
shows two 8251A packages; the
[DSC 2847 front photo](../board/evidence/front-annotated.jpg) shows a
14.400 MHz oscillator near U24/U25. These are capacity and placement
clues, **not** a traced DSC-to-DSU RxD or RxC route. If an eight-bit
character boundary is assumed at the first data symbol, the candidate
LSB-first data bytes are `50 49 78 F0` for `A431` and `EE C5 F4 18` for
`C991`, invariant across the two tested rotations. Repeated `1` sync
bits alone do not establish the actual 8251A character boundary, and no
physical 8251A receive event or controller read has been observed.

The [continuous trace report](results/receiver-mask04-protocol-preamble.json)
and [serial timing report](results/receiver-mask04-serial-candidate.json)
retain input, trace and source hashes, capture events, decisions and
candidate bit times. C3 remains open. The next bounded test should model
the 8251A external-SYNDET character alignment under labelled
SYNDET/RxC/RxD connections, or constrain those pins from the existing board photos;
missing continuity is not a reason to stop. Reproduce from the microcode
directory with `python3 g2/receiver_mask04_protocol_preamble.py` and
`python3 g2/receiver_mask04_serial_candidate.py`.
