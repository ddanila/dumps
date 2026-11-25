# A latched raw-PROM decode can isolate the candidate ADC read

The [DED 3558 photograph](../../../photos/PXL_20261123_114854803.jpg)
shows an ADC0800 beside two 74LS244 buffers. The current joint-map receive
fixture needs a full complementary byte at `3F8`, but exposing that byte at
wrapper `3EB` [ends the loop](RECEIVER-3EB-ADC-ROUTE-SCREEN.md). This screen
asks whether the **real control PROM words** contain a simple candidate
buffer-enable pattern with the right phase. Its gate is a wiring hypothesis,
not a traced U10-to-74LS244 net.

For every reached transition in a 48,047-instruction, 32-sample real-PROM
run under the alternating 0/2 dispatch fixture, the script evaluates raw
U10 output bits. No single literal or two-literal AND of the 32 raw PROM
bits and their complements enables **only** the required `3F8` word.
One three-literal candidate is `!U10.D1 & U10.D3 & U10.D7`:

| Gate phase | Enabled word | Visits | Consequence |
| --- | --- | ---: | --- |
| Same fetched word | `3F7` | 3,000 | Conflicts with its Am27S31 read if wired directly to ADC OE |
| One microinstruction later | `3F8` | 3,000 | Selects every offered ADC byte; no other loop word enabled |

The one-cycle pattern can be produced by a **hypothesized** latch/decode
phase. The script derives its input site from the raw-PROM predicate, feeds
all 3,000 held ADC bytes there, and re-executes the joint map. Its full-state
trace digest equals the earlier `3F8`-only fixture, with every byte selected
by the ALU and the same clean 0/2 control path. This replaces an arbitrary
PC-qualified ADC enable with a concrete candidate control-word decode, but
the photographed latch and buffer connections are unverified.

A negative control explains why the phase and **third** literal matter.
The shorter delayed gate `!U10.D1 & U10.D3` also enables the high-slice D
input at `3FA`. Supplying the ADC byte there makes the run reach `084` after
only 95 `3F8` visits. The low-slice arithmetic listing alone would miss
that high-slice data use. Same-phase use of the three-literal gate would
enable the ADC during `3F7`'s ROM read, so it is an electrically incompatible
same-bus fixture unless a different mux/hold topology is added.

The result narrows a runnable ADC-output-enable hypothesis; it does not
identify the physical PROM-to-buffer route, the 3EC dispatch source, ADC
sample clock, recovered dibit, or USART RxD connection. C3 remains open.
The [machine report](results/receiver-prom-adc-enable-phase.json) includes
gate counts, negative control, trace digests and source/photo hashes. Run
`python3 g2/receiver_prom_adc_enable_phase.py` from the microcode directory.
