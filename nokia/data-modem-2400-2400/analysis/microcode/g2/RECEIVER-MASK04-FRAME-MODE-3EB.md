# A controller frame edge at D3EB changes state but shows no training memory

The [controller A3→A4 replay](CONTROLLER-A3-A4-MODE-EDGE.md) observes a
third CD4094 frame-byte change `81→A1` at A4 entry. The mask-`04`
receive wrapper at `3EB` selects an external D byte, currently an
untraced scenario value `01`. This experiment offers the controller's
**observed bytes** at that input as a labelled photo-compatible
connection hypothesis. It does not claim a CD4094-to-`3EB` wire or that
the frame edge is the echo-freeze command.

First, a held `09` ADC code runs under all 16 `01,11,…,F1` high-nibble
classes at `3EB`. Fifteen complete the 1,500-ADC-visit, four-row loop;
`31` leaves after one ADC visit. Both controller bytes `81` and `A1`
are in the surviving set. Next, the `0,1,3,2` reference waveform and
all-zero-dibit control each run four 48,047-instruction scenarios: held
`81`, held `A1`, `81→A1` and reverse `A1→81`. The synthetic edge occurs
at wrapper visit 3,000 of 6,001, halfway through this shortened
diagnostic receive fixture. All eight runs select 1,500 complementary
ADC bytes, complete all four rows and take the same PC path.

For **both** ADC inputs and both edge directions, complete RAM/Q state
after `3FE` matches the starting held-byte control on every visit before
the edge, then matches the target held-byte control on every completed
visit after it. The per-quarter state-difference counts are `0,0,375,375`
against the start control and `375,375,0,0` against the target. Held `81`
versus `A1` changes R0, R1, R10, R12 and R13 on every fourth-row visit;
Q also changes on 1,171/1,500 waveform and 1,312/1,500 zero-control
visits. The byte route is therefore active, but this tested state has no
observable history of the earlier mode after a completed row.

The edge also changes `3EB` Y on 3,000 wrapper visits relative to the
starting control and changes TEST at `3EA` on 844–892 visits. `3EA` is
PLP and ignores TEST. At the conditional `3EC` and `3ED` words, TEST and
next PC never differ. ADC-dependent complete-state counts in the four
375-visit quarters are identically `281,328,375,328` for all four mode
sequences. The transition changes byte arithmetic but neither exposes a
mode-qualified branch nor freezes an acquired state in this fixture.

This rejects a simple `81→A1` direct-D3EB train/freeze interpretation
under the stated four-row map and shortened timing. Another input lane,
gate, field map or output path remains possible; the physical frame
route is not known. No line residual or USART receive bit is identified,
so C3/C4 stay open and G2 continues.

The [machine report](results/receiver-mask04-frame-mode-3eb.json)
records all held-byte outcomes, eight trace digests, per-byte changes,
edge/control comparisons and source hashes. Reproduce with
`python3 g2/receiver_mask04_frame_mode_3eb.py` from the microcode
directory.
