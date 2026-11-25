# Joint lower-instruction pin changes still do not retain the candidate ADC sample

The earlier [single-pin screen](LOWER-I-ADC-RETENTION-SCREEN.md) changed one
lower Am2901 instruction bit at a time while controller bits entered `D38E`
and a candidate ADC0800 byte entered `D3A1`. Because the translated mapping
couples lower I2 and I7 to one PROM bit, the
[joint screen](receiver_joint_i2_i7_screen.py) now assigns each of those two
pins independently to every raw U11 data bit: **64 real-PROM mappings**.
The [report](results/receiver-joint-i2-i7-screen.json) records each mapping,
input selection, trace digests and state comparisons.

All runs start with Q=5 and zero RAM, execute 320 microinstructions, keep the
real 8031 scrambler-bit stream on the separate `D38E` candidate route, and
offer one `01`, `80` or `FF` byte at `D3A1` visit 20. The physical input and
instruction-pin connections are explicit hypotheses. **40 mappings** select
both inputs through that visit; the other 24, all with I2 taken from U11
bit 1, 5 or 6, cannot test later sample retention in this window.

For the 40 eligible mappings, `01` and `FF` change the modeled state at the
offered sample boundary, while `80` does not. None of the three values
changes a later boundary, selected ROM address, candidate output event, or
PC path. Thus changing both coupled instruction pins still leaves only a
current-byte transient in this `389–3A1` fixture. It does not create
receive-sample history or a recovered bit.

This closes a specific two-pin extension of the existing receiver candidate,
not the ADC0800 receive path in general. The next search should change the
program path or jointly constrain the instruction, address and sample-latch
timing from the photographs. A useful positive criterion is an ADC-dependent
state that survives a later conversion while controller bits remain present,
followed by a bit decision at the USART-01 receive side. C3 remains open;
missing continuity does not stop runnable alternatives.
