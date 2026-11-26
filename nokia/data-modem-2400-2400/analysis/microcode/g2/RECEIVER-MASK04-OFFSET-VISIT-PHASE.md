# Receive decisions across adjacent ADC capture visits

The [frequency-offset replay](RECEIVER-MASK04-FREQUENCY-OFFSET.md) left three
data dibits unknown at +7 Hz with the frozen 47/94-visit receive readout.
This [capture-phase replay](receiver_mask04_offset_visit_phase.py) keeps both
decision tables and the consensus rule frozen, and captures executed `3F8`
Y at visits 46–48 and 93–95 of each symbol. It tests the predeclared pairs
46/93, 47/94 and 48/95 without adding reference labels to either table.
The visits straddle the assumed ADC sample boundaries: 46 and 93 are the
last visits of the preceding samples, while 47 and 94 are the first visits
of the next samples. Thus the alternatives change the sampled PCM values,
not just a latch delay within an unchanged sample.

Six new real-PROM streams use a 32-symbol `11` preamble, 16 seeded data
symbols, initial phases 75°/165° and carrier offsets −7/0/+7 Hz. Each
executes 576,047 words and 18,000 complementary ADC visits. The reference
receiver decodes every input before PROM replay. The table counts both
initial phases, excluding the first differential symbol.

| Seed and offset | 46/93: wrong, unknown, data unknown / 94 | 47/94: wrong, unknown, data unknown / 94 | 48/95: wrong, unknown, data unknown / 94 |
| --- | --- | --- | --- |
| New `C41E`, −7 Hz | 0, 2, 0 | 0, 3, 1 | 0, 3, 1 |
| New `C41E`, 0 Hz | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| New `C41E`, +7 Hz | 0, 2, 0 | 0, 6, 4 | 0, 6, 4 |
| Earlier `A9D4`, +7 Hz | 0, 2, 0 | 0, 6, 3 | 0, 6, 3 |

The earlier seed was replayed after the new-seed result. The original
47/94 metrics reproduce its prior +7 Hz result, providing a same-stream
control. Across the two +7 Hz seeds, 46/93 has **zero unknown data dibits
out of 64**; 47/94 has seven. All three pairs have zero incorrect known
decisions and no conflicts between the two frozen readouts in these runs.
This favors the earlier sample pair as a *working* capture hypothesis. It
does not identify the board's actual latch edge or demonstrate a physical
phase tracker, noise tolerance, arbitrary offsets or USART receive behavior.
The two remaining +7 Hz unknowns at 46/93 are preamble decisions; a full
serial handoff still requires them or a separately justified acquisition
rule. C3 remains open.

The next test should keep 46/93 frozen on new data and a longer stream,
including intermediate carrier offsets and an explicit preamble decision
mechanism. Check a photo-compatible latch/clock route and serial handoff
against the resulting executed output. Do not fill unknown preamble bits
from the expected training pattern when claiming a complete recovered
stream.

The [main machine report](results/receiver-mask04-offset-visit-phase.json)
and [prior-seed replay](results/receiver-mask04-offset-visit-phase-prior-seed.json)
record each trace, ADC hash and source hash. Reproduce the main report from
the microcode directory with `python3 g2/receiver_mask04_offset_visit_phase.py`.
For the prior-seed replay, import that module, set `SEED=0xA9D4` and
`OFFSETS_HZ=(7,)`, then call `run()` with the prior-seed result path.
