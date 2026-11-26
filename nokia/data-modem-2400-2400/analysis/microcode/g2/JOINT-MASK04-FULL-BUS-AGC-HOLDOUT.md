# Non-zero payload holdout for the preamble AGC candidate

The [preamble-calibrated AGC candidate](JOINT-MASK04-FULL-BUS-AGC-CANDIDATE.md)
was frozen after it restored zero-run reception at 0.75 PCM gain and
±16 counts of bias. This holdout applies its **unchanged** target midpoint
(−0.09375), target AC RMS (52.509), first-128-A3-sample calibration window
and later-only correction to the two non-zero line streams recorded before
the AGC was proposed. The full-byte DAC order `[4,0,6,1,3,2,5,7]`,
candidate `127` latch word, line filter, ADC cadence and fixed-first
PROM-byte readout also stay fixed.

The repeated real-PROM transmitter Y7 hashes match the earlier executed
non-zero streams, and the nominal full-byte PCM hashes match the previous
payload holdout. Each of the four corrected cases then executes 780,047
real-PROM receive instructions. The independent reference decoder makes
no errors. The source gain estimates imply correction ratios 1.3335–1.3339.

| Selector | Input change | Frozen 46/93 wrong/unknown data dibits | Margin wrong/unknown | Fixed-first wrong/unknown | Recovered line bytes |
| --- | --- | ---: | ---: | ---: | --- |
| `40` call | 0.75 gain, +16 | 0/2 | 0/0 | 0/0 | `E4 1B C7 39 55 AA 00 FF` |
| `40` call | 0.75 gain, −16 | 0/2 | 0/0 | 0/0 | same |
| `60` answer | 0.75 gain, +16 | 0/9 | 1/0 | 0/0 | `93 6C 2D D2 F0 0F 81 7E` |
| `60` answer | 0.75 gain, −16 | 0/9 | 1/0 | 0/0 | same |

The answer stream exercises all four dibits and all 16 adjacent-dibit
transitions. Its margin error falls at a symbol with a known 46/93
decision, so the frozen fallback does not overwrite that decision.
This verifies that the **modeled** preamble AGC and readout recover varied
data under these four affine level changes, rather than only the zero-run
used to choose the AGC target. It does not establish performance under
unknown carrier phase, noise, drift or actual board gain-control timing.

The AGC remains an assumed external analog stage; no DSC instruction or
photographed net has been identified as its implementation. DAC/ADC wiring,
sample clock, decision gates and USART route also remain open. Continue
with phase/noise challenges and photo-compatible circuit tests. C2/C3
and G2 stay open and active.

Run `python3 g2/joint_mask04_full_bus_agc_holdout.py` from the microcode
directory. The [machine report](results/joint-mask04-full-bus-agc-holdout.json)
records source hashes, calibration values, PROM trace digests, decision
scores and recovered bytes.
