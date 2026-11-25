# A common PROM edge distinguishes two DAC latch phases

The joined transmitter runs produce candidate DAC codes at `129`, but the
photo does not show the 74LS273 clock wire. The real U10 control PROM has
**D2 levels `0,0,1,0`** across both `127–12A` and `12C–12F`. That yields a
rising edge at `129` or `12E`, followed by a falling edge at `12A` or
`12F`. It is a possible common strobe for both loops, not a traced clock.

Two 4,000-instruction real-PROM executions check the edges, using the q3
field map, upper Am27S31 bank, held-I0 fixture and candidate D127 values
`88` and `81`. After the `127` loop begins, held `88` produces **990**
U10 D2 rising edges at `129` and 990 falls at `12A`, with no other U10 D2
edges in that window. Held `81` runs both loops: 125 rise/fall pairs at
`129/12A` and 863 at `12E/12F`. Every reached ROM-output word has the
corresponding edge. The actual first-loop ALU Y values at `128`, `129` and
`12A` are 139, 126 and 141 at the first such transition; clock phase
changes the byte a latch could capture.

The 74LS273 clocks on a rising edge. If a direct U10 D2 edge at the fetch
of `129` arrives before the new ALU Y settles, it captures the prior
`128` value. An inverter or later phase at `12A` could clock the settled
`129` ROM result instead. Neither clock propagation, inverter connection
nor the required rate divider is visible as a verified net. At one
microinstruction per 1–4 periods of the photographed 14.4 MHz oscillator,
the raw edge repeats at 0.9–3.6 MHz, far faster than a 9,600-sample/s DAC
clock.

The earlier [full-PROM free-clock replay](PHOTO-JOINT-FREE-CLOCK-SITES.md)
captured both Y sites through the uninterrupted tone/training/data trace.
For the six DAC bus orders that survived independent nonperiodic dibits,
the [fixed pulse-shape comparison](PHOTO-JOINT-WAVEFORM-SHAPE.md) gives
mean R² **0.530** for `128` and **0.647–0.661** for `129`, a 0.118–0.131
advantage for the ROM-result phase on the same bus. Direct dibit decisions
alone did not distinguish the phases. These comparisons apply to the
`127–12A` loop; they do not validate a `12E` output stream or the analog
line route.

This is a concrete timing discriminator for a photo-compatible latch
hypothesis. Test a rate-qualified, post-ROM clock phase and the 74LS373 /
74LS273 data path before calling `129` the physical DAC byte. C2 remains
open. The [machine report](results/photo-tx-prom-latch-phase.json) contains
the raw levels, edge counts, Y witnesses, six bus comparisons and source
hashes. Reproduce with `python3 g2/photo_tx_prom_latch_phase.py` from the
microcode directory.
