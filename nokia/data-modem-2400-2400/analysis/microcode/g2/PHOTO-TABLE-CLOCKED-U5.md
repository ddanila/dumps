# Candidate U5 clock from raw PROM edges

The earlier [U10-bit route](PHOTO-TABLE-PROMBIT-CONSUMER.md) set candidate U5
Q0 separately for each microword. A real 74LS273 Q output holds its value
between clock edges. This experiment tests that missing state: candidate U5 D0
is inverted U10 data bit 5, and Q0 drives Am2901 I0 and A1. Seven raw PROM
bit edges that matched the necessary levels in an offline trace screen were
replayed as clocks during execution, with either initial Q0 level.

Run `python3 g2/photo_table_clocked_u5_screen.py` from the microcode directory.
The [machine-readable result](results/photo-table-clocked-u5-screen.json)
contains all 168 runs, trace digests, source hashes and each clock hypothesis.
The fixture uses the real four-PROM dumps and four real 8031 USART-01 byte
groups offered at candidate D349. Three saved controller/branch seeds run for
2,500 cycles each; the first 15 arrivals at `084` use a diagnostic AC=RST
pulse. The latch samples its data on the current microword when the chosen
raw PROM bit changes to the specified level.

All 168 runs complete that diagnostic fixture. Every reached sign-table word
has Q0 low and every reached `140/141/143/146` consumer word has Q0 high,
matching the necessary levels from the offline screen. The 728 reached table
calls all retain the exact signed-pair arithmetic, and 896 reads consume
table-written registers downstream. Yet **zero** stateful traces match the
per-microword U10-bit reference trace. Extra latch captures outside those
critical words change execution, so a timing match at selected PCs is not a
validation of a physical clock.

Only U11 data bit 3 on a rising edge gives a nonzero `392/39E` candidate in
this set: 16 runs show late `FF` values. Those values are identical across the
four controller byte groups for a given seed and initial level. They are a
fixed late state, not a command-dependent sample stream. The other 152 runs
show zero at those candidate output words. No tested raw-bit clock meets the
transmitter acceptance check.

The visible board does not trace U10 D5 through an inverter to U5 D0, any of
these clock bits to U5 CLK, or U5 Q0 to both Am2901 controls. Current-word
capture is an explicit timing assumption. The run reads raw PROM dump bits;
it does not prove those clock levels are electrically available under the
candidate enable states, especially for U11 with E4 held high. The result
closes these seven specific raw-edge candidates under this fixture; it leaves decoded clocks,
external clock phases, other data routes and the DAC latch path open. The
next useful test is a photo-compatible clock phase or decoded-enable model
that holds the table/consumer levels **and** produces controller-dependent
output, while checking the proposed byte latch at the DAC pins. Missing
continuity measurements do not block that test.
