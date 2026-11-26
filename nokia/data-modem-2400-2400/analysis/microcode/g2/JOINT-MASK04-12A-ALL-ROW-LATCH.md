# Real-PROM four-row capture narrows the receive latch clock

The [all-row capture](joint_mask04_12a_all_row_latch.py) reruns one of the
previously saved Tx→line→Rx cases with the actual q3/mask-04 PROM dumps:
selector `40`, payload `62 E5 19 A7 D0 3B 8F 54`, R1 offset 88 and 75%
line level. It checks the new transmitter, PCM and receiver trace hashes
against the earlier [fresh 20-state holdout](JOINT-MASK04-12A-ROW0-TWENTY-STATE.md),
then captures **all four** executed `3ED` Y rows, plus `3F8` Y, at receive
visits 46, 47, 93 and 94 in each of 65 symbols. The regenerated trace hashes
match. This is a new real-PROM execution; the DAC, analog and ADC routes are
still the same labelled hypotheses.

Holding each row's bit 0 at visit 46 as the phase rule's seventh bit gives:

| Assumed latch source | Bit-0 values over 65 symbols | Decision errors / 64 |
| --- | --- | ---: |
| `3ED` row 0, qualified clock | 58 ones, 7 zeroes | **0** |
| `3ED` row 1 | 65 zeroes | 20 |
| `3ED` row 2 | 65 zeroes | 20 |
| `3ED` row 3, final value after an every-row clock | 60 ones, 5 zeroes | 14 |

Rows 1 and 2 are zero in every one of the 260 checked symbol/visit
snapshots. A four-bit latch that clocks on every executed `3ED` edge would
overwrite row 0 twice with zero, then retain row 3. Under the proposed
readout, that clock policy makes 14 wrong dibit decisions in this stream.
Row-0 qualification preserves the distinguishing bit and makes none. This
supports a **necessary row qualification or alternate hold path for this
candidate**, not a traced U12 pin or proof of the actual Nokia consumer.

The [machine report](results/joint-mask04-12a-all-row-latch.json) includes
all 260 five-value snapshots, per-row errors, trace digests and source hashes.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_all_row_latch.py
```

C3 remains open. Next test the row-qualified path on the answer selector or
another independently changed carrier/gain fixture, then seek a photographed
source for the row qualifier and remaining capture storage. The untraced
clock is an assumption to vary, not a G2 blocker.
