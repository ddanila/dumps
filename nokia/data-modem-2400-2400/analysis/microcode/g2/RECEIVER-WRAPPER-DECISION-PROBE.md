# The sustained receive wrapper does not expose the tested ADC decision

The [raw-PROM ADC-enable candidate](RECEIVER-PROM-ADC-ENABLE-PHASE.md)
can feed the ADC byte at `3F8` while preserving a 0/2 dispatch loop. To see
whether that loop turns its changing state into a receive decision, this
probe compares two 32-sample reference waveforms: dibit pattern `0,1,3,2`
and all-zero dibits. Both run for 48,047 instructions, select 3,000 ADC
bytes at `3F8`, and complete cleanly under the same joint mapping and
94/94/94/93-visit sample hold. The generated ADC waveforms differ, and so
do their full-state trace digests.

At every visit to wrapper words `3EA`–`3ED` and the two reached table rows
`3EF`–`3F2` and `3F7`–`3FA`, the probe records TEST, next PC, Q, ALU Y,
sign, zero, carry and overflow. The two streams differ
at 4,137 Q values at **each** wrapper word. They differ at **zero** TEST,
next-PC, Y or flag values there. `3EA`'s varying TEST and Y are therefore
the same wrapper cadence in both streams, not an observed receive decision.
`3EC`'s alternating next PC is the assumed 0/2 dispatch and is likewise
identical between streams. `3EE` is not reached.

The table rows have input-dependent arithmetic but still no changed TEST or
next PC. Selected differences out of 3,000 row visits are:

| Word | ALU Y differences | Q differences | Changed ALU flags |
| --- | ---: | ---: | --- |
| `3F0` | 2,241 | 2,241 | sign 257, zero 189, carry 257 |
| `3F1` | 2,241 | 1,895 | sign 1,024, overflow 1,024 |
| `3F8` | 2,781 | 1,895 | sign 1,686, zero 368, carry 282 |
| `3F9` | 2,787 | 2,242 | sign 197, carry 1,166, overflow 197 |
| `3FA` | 2,298 | 2,242 | none |

This excludes an ADC-dependent branch at these reached words and a direct
ALU decision at the four wrapper words **for this fixture**. It does not
exclude a decision made from the row arithmetic by a separate latch, a
stateful readout of Q/RAM, or a different dispatch, clock or ADC route.
The prior [fixed-phase row flag screen](RECEIVER-TWO-ROW-DECISION.md) found
no generalizing dibit bit on these flags. Next test a photo-compatible
output-latch/USART RxD candidate or a distinct condition path. Keep C3 open
and G2 active; an untraced wire does not prevent that test.

The [machine report](results/receiver-wrapper-decision-probe.json) records
every field count, first difference, stimulus and trace digest. Reproduce
with `python3 g2/receiver_wrapper_decision_probe.py` from the microcode
directory.
