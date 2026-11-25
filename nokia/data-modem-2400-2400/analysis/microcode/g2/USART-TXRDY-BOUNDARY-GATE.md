# TxRDY gives a phase-independent candidate for the A3→A4 bit boundary

The [TxRDY-paced controller run](MAIN-LOOP-USART-TXREADY.md) models a
one-byte 8251A transmit buffer and a 2400-bit/s shifter. The
[Intel 8251A datasheet](https://deramp.com/downloads/intel/8251A.pdf)
distinguishes TxEMPTY, which falls when the CPU writes a data character,
from TxRDY, which reports that the transmit-data buffer has emptied. In
the paced model, the first TxRDY rise after A4's first write occurs when
the shifter takes that byte and emits its first bit.

The [event screen](usart_txready_boundary_gate.py) checks all eight sampled
byte-clock phases for each `40`/GPC and `60`/GPA controller path. The time
from TxEMPTY fall at the CPU write to the first data bit requires **1–8 Tx
clock edges**, depending on phase. Thus a fixed number of edges after
TxEMPTY cannot identify the data boundary in every tested case. The modeled
TxRDY rise does identify it without that phase-dependent wait.

The first data bit is the known bridge bit (`1` for GPC, `0` for GPA). A
labelled downstream decoder could detect the first TxRDY rise after a queued
data byte, disregard that first shifted bit, and pair the next 64 data bits
as segment 2. If it uses the last 64 `FF`-fill bits for segment 1, the
resulting 64 dibits are **symbol-for-symbol identical to the inputs of the prior
real-PROM continuous DSC runs**. Those runs give 0/62 aligned reference
decoder errors on all 12 candidate DAC buses for both selectors. Keeping a
fixed raw bit pairing instead gives 0/62 for GPC and 1/62 for GPA in the
best tested offset.

The paced controller model supplies at least 64 fill bits after A3 entry at
three sampled phases for GPC (`0`, `416`, `2912` ticks) and five for GPA
(`0`, `416`, `832`, `2496`, `2912`). Phases `0`, `416` and `2912` work for
both selectors. This supports the *timing capacity* for 32 reversal
symbols followed by the calibrated segment-2 input; it does not locate the
physical start of segment 1.

The TxRDY-to-decoder route, first-bit discard, DSC input gate and DAC clock
remain untraced. A TxRDY pin may also be conditioned by CTS and transmitter
enable, both assumed permissive here. The real-PROM scores above are reused
only after checking that the event-derived dibits exactly equal the prior
PROM inputs; this screen does not claim a new DSC run or a physical line
waveform. The [machine report](results/usart-txrdy-boundary-gate.json)
retains all 16 event timings, candidate input checks, trace digests and
source hashes. The next experiment should inspect the photographed 8251A
TxRDY/TxEMPTY vicinity for a plausible clocked gate, then exercise any
photo-compatible route through the actual DSC input and DAC sample clock.

The [first-byte alignment screen](USART-DATA-START-ALIGNMENT.md) now checks
all nine possible starts in the first transmitted data byte. Only a one-bit
skip gives zero standard-labelled decisions in both modes; adjacent offsets
were exercised in new real-PROM control runs. This sharpens the timing
constraint without identifying the physical gate.
