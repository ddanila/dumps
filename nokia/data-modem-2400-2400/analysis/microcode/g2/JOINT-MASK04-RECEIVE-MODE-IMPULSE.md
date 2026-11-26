# Observed controller mode bytes do not add impulse memory at direct D3EB

The [matched-tail ADC impulse](JOINT-MASK04-RECEIVE-IMPULSE-MEMORY.md)
found no persistent post-visit difference at its selected capture
points with the receive wrapper's assumed `D3EB=01`. A later
[full-word trace](JOINT-MASK04-RECEIVE-PULSE-CARRYOVER.md) finds brief
pre-`3F8` carryover in that `01` case. The controller actually emits
frame bytes `81` and `A1`
around the A3→A4 boundary. This test offers each byte as a **held,
hypothetical direct D input at `3EB`**, alongside `01`, to ask whether
that mode choice changes the impulse response. It does not assert the
controller frame wire or that `81→A1` is an echo-freeze command.

Nine real-PROM runs use the same varying eight-symbol ADC waveform,
four-row mask-`04` mapping and 96,047-instruction receive window. Within
each mode, baseline `51` at sample 25 is compared with a single
high-nibble change to `B1` or a low-nibble-only change to `5E`; all
later ADC samples are identical. The `01` cases reproduce the earlier
saved trace, state and ADC hashes exactly. All nine PC-sequence digests
match, and every run completes 3,000 ADC visits.

| Held `3EB` D | Channels changed during the 47-visit high-nibble pulse | Changed captured visits after input rejoins | Low-nibble control |
| --- | --- | ---: | --- |
| `01` | `3F8`/`3F9`/`3FA` Y, Q, R1, R12 | 0 | Captured state and trace digest unchanged |
| `81` | same | 0 | same |
| `A1` | `3F8`/`3F9`/`3FA` Y, Q, R1 | 0 | same |

The held mode bytes change the overall execution-state digest relative
to one another, so the candidate input is active. They do not make this
ADC pulse persist beyond its sample, and the captured post-`3FA`
`3ED` Y does not change in this fixture. The previously tested `81→A1`
edge also failed to freeze acquired state under a direct `3EB` route;
this pulse test adds a matched-input, varying-waveform control rather
than only comparing mode histories.

This rejects **only** cross-sample memory through the tested direct
`3EB` D lane with held `01/81/A1`, the fixed four-row dispatch and no
external RAM feedback. A mode-qualified write gate, different return
lane, TEST condition or output latch can behave differently. C3/C4
remain open and G2 active. Next test a photo-compatible external RAM
feedback/clock route with a common-tail pulse and a no-feedback control,
then require a selective echo or recovered-bit output before assigning
the modem function.

Run `python3 g2/joint_mask04_receive_mode_impulse.py` from the
microcode directory. The [machine report](results/joint-mask04-receive-mode-impulse.json)
records per-channel difference windows, source hashes, PC and full
execution-state digests.
