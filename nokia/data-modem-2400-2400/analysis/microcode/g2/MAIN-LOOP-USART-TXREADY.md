# TxRDY pacing preserves the segment-2 bytes across the A4→A5 boundary

The earlier [Timer-1 controller run](MAIN-LOOP-TIMER1-SEGMENT2.md) held
the 8251A status bit TxRDY high. It produced eight `FF`-source port-`01`
bytes during A4 and the first `03`-source byte in A5, but it did not make
the CPU wait for the USART transmit buffer. The
[Intel 8251A datasheet](https://deramp.com/downloads/intel/8251A.pdf)
defines the TxRDY **status bit** as transmit-data-buffer empty. This
[replay](main_loop_usart_txready.py) supplies that bit from a one-byte
buffer and shifts TxD at an assumed 2400-bit/s clock. The clock is exactly
416 modeled 8031 machine-cycle ticks per bit if the photographed 11.9808 MHz
oscillator feeds a classic 12-clock core. Eight byte-clock phases, one bit
apart, are tested for each controller selector.

| Selector | A4 `FF` writes | First A5 write | Second A5 write | First nine TxD bytes |
| --- | ---: | --- | --- | --- |
| `40` / GPC | 7 | `31` from `FF` | `FC` from `03` | `F9 07 F8 1C 1C F0 81 31 FC` |
| `60` / GPA | 7 | `D9` from `FF` | `D9` from `03` | `F8 07 F8 9C 0F C2 09 D9 D9` |

All 16 runs complete the 8031 A1→A2→A3→A4→A5 path without an attempted
write to a full USART buffer. A4 takes 24–28 polling passes instead of eight.
In each run the first nine bytes are **actually shifted by the modeled TxD**,
and bits 1–64 from the first data byte match the exact V.26 ter GPC or GPA
segment-2 pattern. TxRDY pacing therefore moves a state label at the eighth
`FF` byte; it does **not** remove that byte or the digital pattern.

The same model automatically shifts `FF` sync characters while the data
buffer is empty. From the first modeled A3 state entry to the first data bit,
the sampled phases yield 59–66 fill bits for GPC and 61–68 for GPA. Several
phases allow at least 64 consecutive `1` bits after A3 entry; a 32-symbol
segment-1 window is therefore compatible with the modeled timing. Its exact
start relative to A3 and to the USART character boundary remains unknown.
The [one-bit bridge](USART-SYNC-FILL-SEGMENT1.md) between that fill and the
standard segment-2 window remains in the raw TxD stream.

The controller still uses an explicit RAM15-positive gate, synthetic
received bytes and CD4094 serial-completion events. The 2400 Hz Tx clock,
initial `FF` shifter, CTS permission and TxD-to-DSC route are assumptions;
only eight of 3,328 possible byte-clock phases were sampled. The model does
not establish the physical DAC or line signal, or the DSC receiver/echo
canceller. The [machine report](results/main-loop-usart-txready.json) stores
each clock phase, controller timing, writes, transmitted bytes and source
hashes. Next carry the paced TxD bit events and an explicit TxEMPTY/clock
alignment into the DSC input candidate, preserving the bridge bit.
