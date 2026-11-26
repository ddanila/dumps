# Real-PROM four-row capture narrows the receive latch clock

The [call-side all-row capture](joint_mask04_12a_all_row_latch.py) and
[answer-side repeat](joint_mask04_12a_all_row_answer.py) rerun both fresh
payloads with the actual q3/mask-04 PROM dumps at R1 offset 88 and 75% line
level. They check the new transmitter, PCM and receiver trace hashes against
the earlier [fresh 20-state holdout](JOINT-MASK04-12A-ROW0-TWENTY-STATE.md),
then capture **all four** executed `3ED` Y rows, plus `3F8` Y, at receive
visits 46, 47, 93 and 94 in each of 65 symbols. Both regenerated trace
hashes match. These are new real-PROM executions; the DAC, analog and ADC
routes are still the same labelled hypotheses.

Holding each row's bit 0 at visit 46 as the phase rule's seventh bit gives:

| Assumed latch source | Call `40` bit 0 / errors | Answer `60` bit 0 / errors |
| --- | --- | --- |
| `3ED` row 0, qualified clock | 58 ones, 7 zeroes; **0/64** | 58 ones, 7 zeroes; **0/64** |
| `3ED` row 1 | 65 zeroes; 20/64 | 65 zeroes; 21/64 |
| `3ED` row 2 | 65 zeroes; 20/64 | 65 zeroes; 21/64 |
| `3ED` row 3, final value after an every-row clock | 60 ones, 5 zeroes; 14/64 | 57 ones, 8 zeroes; 19/64 |

Rows 1 and 2 are zero in every one of the 520 checked symbol/visit
snapshots across the two runs. A four-bit latch that clocks on every executed
`3ED` edge would overwrite row 0 twice with zero, then retain row 3. Under
the proposed readout, that clock policy makes 14 and 19 wrong dibit decisions.
Row-0 qualification preserves the distinguishing bit and makes none. This
supports a **necessary row qualification or alternate hold path for this
candidate**, not a traced U12 pin or proof of the actual Nokia consumer.

The [counter-phase screen](joint_mask04_12a_u24_phase_screen.py) makes the
pictured U24 74LS161 a specific, still hypothetical qualifier. Assuming its
low bits count `00→01→10→11` over the four `3ED` rows, it tries all four
two-bit decodes both before and after an increment at the candidate raw-PROM
`3ED→3EA` edge. Only pre-increment `00` (or equivalently post-increment `01`)
selects row 0 and leaves both streams error-free. The other six decoded
phases make 14–21 errors; an unqualified edge makes 14/19. This fixes the
required **logical counter phase under that candidate**. It does not show
that U24 actually clocks on `3ED`, drives U19, or resets at row 0. The
[phase report](results/joint-mask04-12a-u24-phase-screen.json) preserves the
eight alternatives per selector. Reproduce with
`python3 g2/joint_mask04_12a_u24_phase_screen.py`.

The [call report](results/joint-mask04-12a-all-row-latch.json) and
[answer report](results/joint-mask04-12a-all-row-answer.json) include all 520
five-value snapshots, per-row errors, trace digests and source hashes.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_all_row_latch.py
python3 g2/joint_mask04_12a_all_row_answer.py
```

C3 remains open. Next test a changed carrier/gain fixture, then seek a
photographed source for the row qualifier and remaining capture storage.
The untraced clock is an assumption to vary, not a G2 blocker.
