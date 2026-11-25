# Only one first-byte bit alignment preserves both segment-2 patterns

The [DSU 3556 front photograph](../../../photos/PXL_20261123_114723348.jpg)
shows the two 8251A packages and nearby digital logic, but does not establish
the TxD/TxRDY route to DSC 2847. The
[paced 8251A replay](MAIN-LOOP-USART-TXREADY.md) nevertheless supplies a
testable digital source. At its sampled byte-clock phase 0, both controller
selectors have at least 64 `FF`-fill bits after A3 entry, then transmit the
recorded nine A4/A5 bytes at 2400 bit/s. This
[alignment screen](usart_data_start_alignment.py) takes the last 64 fill
bits as 32 `11` symbols and tries starting the next 32 dibits at every bit
position 0–8 of the data stream. The target is the V.26 ter 32-symbol
segment-1 reversal followed by the 32-symbol GPC or GPA segment-2 pattern.

| Data bits skipped after TxRDY rise | GPC errors / 62 | GPA errors / 62 |
| ---: | ---: | ---: |
| 0 | 15 | 16 |
| **1** | **0** | **0** |
| 2 | 14 | 18 |
| 3–8 | 18–25 | 19–25 |

All 12 surviving photo-B5-compatible DAC bus orders give the same counts in
each row. Skipping the first shifted data bit is the **only** tested alignment
with zero errors for both controller modes. It is also the only offset that
offers the exact standard dibit sequence, so the result is not caused by an
unusually forgiving reference decoder. The `40`/skip-0 and `60`/skip-2
neighboring controls were each run for **768,256 real-PROM microinstructions**
with **192,054 checked PC129 ROM/Y visits**. The skip-1 inputs equal the two
previously executed continuous PROM inputs symbol for symbol, including their
sample digests and zero-error decisions. Other offsets use the independently
checked q3 ROM/Y recurrence and were not separately executed.

The screen constrains a possible USART-to-DSC decoder: if this q3 input
path is the transmitter, it must align to the second data bit at the
fill-to-data transition. A TxRDY-triggered first-bit discard is one labelled
circuit hypothesis; the photograph does not prove it, and a different
pairing/timing circuit could implement the same alignment. The DAC bus and
clock, analog output, 2100 Hz state, DSC receiver and echo canceller remain
unverified, so C2–C4 stay open. The
[machine report](results/usart-data-start-alignment.json) retains all 18
alignment scores, real-PROM control digests and source hashes. Continue by
testing photo-compatible DAC sampling and output shaping; missing net
continuity is not a goal blocker.
