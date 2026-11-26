# Candidate row capture and serial timing from executed receive snapshots

The [event replay](joint_mask04_12a_row0_serial_timing.py) uses the six saved
real-PROM Tx→line→Rx traces from the [fresh 20-state holdout](JOINT-MASK04-12A-ROW0-TWENTY-STATE.md).
It places the executed `3ED` row-0 bit and two `3F8` Y values into separate,
assumed capture stages, applies the frozen phase gates, then presents the two
decision bits to a narrow external-sync 8251A model at candidate RxC edges.
The resulting eight line octets are passed to the executed 8031 receiver
probe. This is a replay of saved PROM observations, not a new PROM run or an
identified Nokia netlist.

The receive loop takes 32 microcycles per ADC visit. The row-0 `3ED` output
is placed at cycle `50 + 32·visit`, and `3F8` Y at `63 + 32·visit`, matching
the previously captured loop schedule. At visit 46, the row bit and first Y
are available by symbol cycles 1,522 and 1,535. The second Y at visit 93 is
available by cycle 3,039. With 12,000 microcycles per 1,200-baud symbol and
an assumed 6,000-cycle bit clock, RxC samples at symbol cycles 6,000 and
12,000. The first bit has **2,961 cycles of setup** after the last required
snapshot. The first reversal dibit is supplied by the known preamble fixture
because differential detection cannot recover it.

| Capture/clock hypothesis | Decision errors across six traces | Serial result |
| --- | ---: | --- |
| Row-0 visit 46; first Y 46; second Y 93; RxC at 6,000/12,000 | 0 in every trace | Eight exact line bytes and eight exact decoded source bytes; no controller errors or overruns |
| Row-0 visit 47 instead | 0 in every trace | Same bytes; row bit is stable over this one-visit interval |
| Row-3 bit at visit 46 instead of row 0 | 14–25 per trace | Wrong line and decoded bytes |
| First Y at visit 47 instead of 46 | 6–10 per trace | Wrong line and decoded bytes |
| Second Y at visit 94 instead of 93 | 10–16 per trace | Wrong line and decoded bytes |
| First RxC at cycle 3,000, then every 6,000 | 64 data-bearing first-bit edges precede the phase result | No complete receive octets claimed |

An aligned SYNDET pulse is asserted at bit 66, the first data bit after the
32-symbol reversal preamble and one pipeline symbol. The separate
[sync timing test](RECEIVER-MASK04-EXTERNAL-SYNC-HANDOFF.md) already shows
that one-bit-early and one-bit-late pulses fail. The precise latch edge matters
more here than the row-bit edge: the row bit tolerates one visit, while either
Y snapshot does not on these streams.

The pictured four-bit U12 could hold only part of the seven-bit state. More
storage, capture qualification, phase/differential logic, a two-bit serializer,
RxD/RxC wiring and SYNDET source remain **explicit circuit assumptions**.
This test establishes a feasible cycle budget and excludes the tested wrong
capture edges; it does not establish that the board implements those gates or
pass C3. Next run a real-PROM capture with all four `3ED` rows at the disputed
visits, then test an every-row latch clock against row-0-qualified capture.
The missing physical connections are not a G2 blocker.

The [machine report](results/joint-mask04-12a-row0-serial-timing.json) saves
per-case errors, RxC availability, selected event cycles, USART octets and
controller bytes. Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_row0_serial_timing.py
```
