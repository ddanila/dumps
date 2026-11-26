# A narrow sample-clock phase fits the executed receive loop

The DSC 2847 photograph identifies a 14.400 MHz oscillator near a
74LS161 counter (U24) and a dual flip-flop (U25); a 74LS169 counter
(U28) sits nearer the PROM bank. Those are timing candidates by part
marking and placement, not traced nets. If one oscillator period is one
microinstruction, the executed four-row receive loop takes 32 cycles
per ADC visit. At 1,200 symbols/s, its 375 visits per symbol occupy
exactly 12,000 cycles. Eight reference samples per symbol then require
1,500 cycles per sample, or 9,600 samples/s. A divide-by-eight sample
counter would provide the symbol rate and a divide-by-four tap could
provide 2,400 RxC edges/s; the source of the divide-by-1,500 sample
clock and actual counter assignments remain unknown.

The [clock replay](receiver_mask04_sample_clock_phase.py) reruns the
192,047-instruction, seed-`4E11`, 45° receive fixture. It verifies
6,000 executed `3F8` visits at a 32-cycle cadence, 6,000 candidate
`3F8→3F9` latch edges and one startup edge. For each phase from −32 to
+32 microcycles relative to the first latch edge, it compares a
1,500-cycle sample clock's index against the ADC sample index actually
offered to every `3F8` visit. It rejects a phase if any visit receives
the wrong sample index or if a sample-clock tick coincides with a latch
edge.

| Sample-clock phase | Result |
| ---: | --- |
| −3, −2, −1 microcycles | Match all 6,000 visits; no same-cycle sample/latch event |
| 0 | Matches the indices but coincides with a latch edge every eight samples |
| Other phases in −32…+32 | At least one wrong sample index or edge collision |

Under the three clean phases, visits 47 and 94 are the **first** executed
reads of reference sample indices 1 and 2 within every symbol. The row-3
`3ED` observation after visit 94 makes both captured features available
at cycle 3,082 of the first symbol. If the first RxC rising edge is
placed at sample-clock index 3 and the second at index 7, they are
6,000 microcycles apart and the first has 1,478–1,480 cycles of setup
after the proposed decision launch. A sample-index-2 first edge arrives
20–22 cycles **before** that launch. This excludes that early RxC phase
for the two-visit readout, under the stated timing model.

This establishes a compatible clock *schedule* using executed PROM
timing. It does not establish the oscillator-to-sequencer connection,
the divide-by-1,500 circuit, U24/U28 counter wiring, counter reset,
RxC driver, latch setup time or physical symbol phase. The modeled
47/46-visit ADC hold is an input fixture, so the narrow phase window
constrains that fixture rather than measuring the Nokia ADC clock.
Test the visible counter/oscillator routes or a natural phase-sensitive
receive stream before selecting one capture phase or closing C3.

The [machine report](results/receiver-mask04-sample-clock-phase.json)
retains every screened phase, 32 selected row-3 times, trace digest and
source hashes. Reproduce from the microcode directory with
`python3 g2/receiver_mask04_sample_clock_phase.py`.
