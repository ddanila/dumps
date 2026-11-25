# Raw PROM bits clock every visit to the D127 transient sites

The [edge screen](photo_127_clock_screen.py) checks every rising and falling
edge of each raw U10/U11/U17/U18 data bit in the held-I0, Q=0, `q3` D127
loop. With D127 fixed at 48 or 56, there are 740 visits each to `129` and
`12A` in 3,000 real-PROM microinstructions. Eleven single-bit edge choices
occur at **every** `129` visit; six occur at **every** `12A` visit. The sets
are the same for both increments. The [report](results/photo-127-clock-screen.json)
lists their chip, bit, polarity and extra edges elsewhere in the trace.

The aligned edges offer specific clock pins to examine, but no edge is a
traced LS273 clock. Each would clock the latch once per four-instruction
quartet, and each also has 5–13 edges outside the repeating site in this
3,000-cycle trace. At the plan's hypothetical 14.4 MHz oscillator divided by
`k=1…4` per microinstruction, an unqualified aligned edge would run at
**0.9–3.6 MHz**, not the proposed 9,600 samples/s. Making a four-word loop
itself run at 9,600 visits/s would require **375 oscillator periods per
microinstruction**. The actual sequencer divider is unmeasured.

Together with the [operand-liveness result](PHOTO-127-LIVENESS.md), this
means a direct single-PROM-bit clock at `129` or `12A` does not yet explain a
DAC sample stream under the fast-clock hypothesis. A divided or gated clock,
another repeated output path, or a different sequencer rate remains possible.
The data-bit route to the photographed DAC08 and the LS273 clock net remain
assumptions to test, not blockers.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_clock_screen.py
```
