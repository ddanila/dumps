# A three-input PROM decode can clock the ADC-sensitive third-row byte

The [caller handoff](RECEIVER-FOUR-ROW-CALLER-HANDOFF.md) showed that the
receive table's `3F7–3FA` row contains input-dependent state that the
following `3FB–3FE` row erases. This screen looks for a **raw control-PROM
decode**, rather than an arbitrary PC-qualified latch, that could capture
the third-row Y byte in between. It runs the same joint upper-source
mask-08 mapping, assumed four-row dispatch and inverted previous-overflow
condition with real controller/PROM instructions.

Across the first 200 executed words, an exhaustive screen of the 32 raw
PROM data bits and their complements finds no one- or two-literal AND that
is high only at `3FA`. It finds exactly two three-literal choices:

| Gate high at `3FA` | High visits in each full trace | NAND rising edge |
| --- | ---: | --- |
| `U10.D3 & U10.D6 & U17.D1` | 1,500 | `3FA→3ED`, 1,500 |
| `U10.D3 & U11.D2 & U17.D1` | 1,500 | `3FA→3ED`, 1,500 |

The full check uses five distinct 32-sample reference inputs, each held as
complementary ADC bytes for 47/46 table visits per sample. Each real-PROM
trace selects all 1,500 ADC bytes. For **both** gates, the AND is high only
at `3FA` and falls on the transition to `3ED`, with no extra edge anywhere
in the run. A three-input NAND would therefore rise at that transition.
The photographed DSC2847 inventory identifies U19 as an SN74LS10N; [TI's
datasheet](https://www.ti.com/lit/ds/symlink/sn74ls10.pdf) confirms that
this part contains three independent three-input NAND gates. This is a
compatible logic topology, **not** a traced U10/U11/U17→U19→latch net.

If that rising edge clocks a latch before `3ED` changes the ALU output, it
captures the previous `3FA` Y byte. Both gate choices capture identical
1,500-byte sequences in each run. Against the all-zero-dibit control, the
other four inputs change 440, 382, 164 and 382 captured bytes respectively.
The byte stream is thus input-sensitive under the stated phase assumption.
No clock divider, bus destination or USART-01 RxD connection is identified,
and the captured bytes are **not** an executed dibit decision. C3 remains
open. The next test should constrain whether a photographed latch receives
this decode and whether a subsequent executed readout uses its bytes.

The [machine report](results/receiver-prom-row-latch-gate.json) records the
minimal gates, full-trace digests, edge counts, byte hashes, input contrasts
and source/photo hashes. Reproduce with
`python3 g2/receiver_prom_row_latch_gate.py` from the microcode directory.
