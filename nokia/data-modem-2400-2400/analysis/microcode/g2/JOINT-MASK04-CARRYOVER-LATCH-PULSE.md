# A row-0-qualified external latch can preserve the previous ADC nibble

The [full-word matched-tail trace](JOINT-MASK04-RECEIVE-PULSE-CARRYOVER.md)
found a 21-microinstruction previous-sample window before the next
identical ADC byte is selected. This [real-PROM edge replay](joint_mask04_carryover_latch_pulse.py)
tests whether the existing [U19/U12 candidate](RECEIVER-MASK04-U12-LATCH-REPLAY.md)
could hold that value until row 3. It uses the same varying 64-sample
baseline and sample-25 `51→B1` pulse; both runs complete **96,047 PROM
words** and **3,000 ADC visits** and reproduce the earlier full-trace
digests.

The three-literal raw-PROM decode `U11.D7 & U17.D3 & U18.D5` gives
**12,000 falling decode edges**, each after `3ED`. A proposed
modulo-four qualifier clocks the pictured four-bit U12 only on row 0,
capturing Y's low nibble. The control clocks U12 after every row and
therefore overwrites row 0 before the row-3 consumer.

| Matched visit window | Qualified row-0 nibble differences | Live row-3 Y[2:0] differences | Every-row latch value before row 3 |
| --- | ---: | ---: | ---: |
| 47 visits holding the altered sample | 46 | 47 | 0 |
| First identical-input visit after pulse | **1** | **0** | 0 |
| Remaining 1,780 visits | 0 | 0 | 0 |

At that first restored visit (ADC visit 1,219), the row-0 edge at cycle
39,058 captures `0` in the baseline and `5` in the pulse run. The next
`3F8` read selects the same current ADC byte at cycle 39,071, and the
DSC's modeled state rejoins at 39,073. Yet at the row-3 edge at cycle
**39,082**, the qualified U12 still holds `0/5` while live row-3
Y[2:0] is `2/2`. An unqualified latch holds `0/0` instead. The
qualifier therefore supplies an explicit, photo-compatible way to
present **previous and current sample information together** after
the internal transient has vanished.

The raw decode is an executed PROM timing fact under the candidate
field map. The U19 gate wiring, row counter/qualifier, Y-to-U12 bits,
row-3 consumer and USART-01 connection remain untraced assumptions.
The earlier [two-phase U12 decision test](RECEIVER-MASK04-U12-LATCH-REPLAY.md)
gets 0/12 errors at 0° but 10/12 at 45° with this qualifier. This
matched-tail pulse proves causal sample retention in the *modeled latch*,
not a phase-robust received bit or C3. Seek a photo-compatible
phase-tracking consumer of the two values and test it on new carrier
phases and payloads. G2 and C3 remain active and open.

Run `python3 g2/joint_mask04_carryover_latch_pulse.py` from the microcode
directory. The [machine report](results/joint-mask04-carryover-latch-pulse.json)
records edge counts, window differences, capture cycles, hashes and
source files.
