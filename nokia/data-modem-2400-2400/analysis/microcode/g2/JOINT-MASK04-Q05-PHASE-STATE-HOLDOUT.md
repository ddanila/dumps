# A frozen four-state receiver rule joins the `12A` line to the 8031

The [development key audit](JOINT-MASK04-Q05-RECEIVE-KEY-COLLISIONS.md)
identified four conflict-free states from executed `3F8` Y at ADC
visits 46 and 93. This [holdout](joint_mask04_q05_phase_state_holdout.py)
freezes `5→0`, `8→1`, `C→2`, `D→3` as phase quadrants before touching
the second nonzero eight-byte payload in each selector mode. Each
dibit is the quadrant difference minus the 180° carrier advance,
mapped by the reference dibit order. The rule fits all 64 development
data decisions, but the following scores use separate payloads.

Both second-payload transmitters reproduce their saved real-PROM trace
and `12A` sample hashes. Their Q=0.5 line PCM hashes match the earlier
holdout, and the independent known-carrier decoder remains exact.
Passing those samples as complementary ADC bytes through two new
real-PROM mask-04 receiver runs gives:

| Selector | Preamble/pipeline decisions | Data decisions | Recovered line bytes | Aligned modeled 8031 result |
| --- | ---: | ---: | --- | --- |
| `40` | 32/32 | 32/32 | `60 65 AF 02 56 8B 78 D7` | `42 DB 19 E7 24 B6 68 93` |
| `60` | 32/32 | 32/32 | `E7 19 5D 73 DC D5 20 2A` | `42 DB 19 E7 24 B6 68 93` |

The modeled 8251/8031 receives the **correct** eight bytes only at
the aligned external SYNDET pulse among the tested one-bit-early,
aligned and one-bit-late placements. The aligned pulse descrambles
exactly the payload in both modes and leaves the controller
in state `AF`, as expected for nonzero bytes. The early control consumes
eight misaligned bytes; the late control consumes only seven. This is
the first full nonzero controller-bit → ROM-sensitive `12A` DAC candidate
→ Q=0.5 line → executed DSC receiver → frozen four-state readout →
modeled USART → unchanged 8031 chain in this fixture.

The four-state mapping and difference operation are **external circuit
hypotheses**, not executed DSC instructions or traced Nokia gates. DAC,
filter, ADC, latch, RxD/RxC and SYNDET wiring and clocks remain
assumed. The handoff therefore strengthens the conditional C2/C3
mechanism but does not pass physical C2 or C3. Challenge new phase,
level and timing fixtures, and test photo-compatible implementation of
the four-state and serial logic without waiting for pin continuity.

The [machine report](results/joint-mask04-q05-phase-state-holdout.json)
records the phase rule, all states/dibits, line and receiver hashes,
recovered bytes and controller control outcomes. Reproduce with
`python3 g2/joint_mask04_q05_phase_state_holdout.py` from the
microcode directory.
