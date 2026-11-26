# Candidate latch phase is mostly insensitive within a 9,600 Hz period

The [phase-accumulator execution](JOINT-MASK04-TX-PHASE-ACCUMULATOR.md)
verified `R1 += D127 (mod 256)` at 54,053 consecutive `127` visits per
selector and `Y7 = R1 bit 7` at all four loop words. This
[phase sweep](joint_mask04_latch_phase_sweep.py) applies that recurrence to
the full controller-derived A1–A4 D127 fixture. Its zero-offset 832 Y7
samples **match every bit** of the saved 1,248,256-instruction real-PROM
run for both call and answer; the four directly captured loop words also
agree with one another. Other offsets are projected from the verified
recurrence, not separately captured full-PROM traces.

At the candidate 14.4 MHz microcycle and 9,600 Hz sample clock, one
sample period spans 1,500 microinstructions or 375 four-word-loop visits.
The sweep captures Y7 at each of those 375 possible visit offsets, assigns
the bit to DAC08 B5's eight-count weight, and applies the previously
declared A2 mid-code gate, Q=1 bandpass and fixed receive alignment.

| Selector | Latch offsets | 2,100 Hz tone peak | Zero-error A3/A4 offsets | Other offsets |
| --- | ---: | ---: | ---: | ---: |
| `40` call | 375 | 375/375 | 328/375 | 47 with one error |
| `60` answer | 375 | 375/375 | 328/375 | 47 with one error |

All 47 nonzero-error offsets miss the same decision index 42 under the
fixed external receive sample shift; no offset has more than one wrong
decision. This means the candidate carrier does not depend on picking a
special loop visit for the latch. The *complete zero-error receive score*
does depend on latch phase or receive alignment at one symbol, so the
original phase-zero result is not evidence for a uniquely correct clock
edge. The sweep does not establish the actual 74LS273 clock, Y7→D4 wire,
DAC output path or an onboard decoder. C2 stays open.

The [machine report](results/joint-mask04-latch-phase-sweep.json) records
every offset and error index. Reproduce from the microcode directory with
`python3 g2/joint_mask04_latch_phase_sweep.py`.
