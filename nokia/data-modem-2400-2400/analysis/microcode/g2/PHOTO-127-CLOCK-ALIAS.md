# Fast-clock gating aliases the D127 B5 tone candidate

The [photo-B5 step screen](PHOTO-DAC-B5-TONE-STEP.md) treated every PC129
visit as one 9,600 Hz DAC sample. Under that assumption, held D127 values
48 and 56 gave B5 peaks at 1,800 and 2,100 Hz. The DSC2847 photograph shows
a 14.4 MHz oscillator, but its divider and the DAC-side 74LS273 clock are
untraced. This [timing screen](photo_127_clock_alias.py) tests the alternative
fast-clock hypotheses already used in the [raw-edge study](PHOTO-127-CLOCK-SCREEN.md):
one microinstruction per `k=1,2,3,4` oscillator periods, with PC129 reached
once every four microinstructions and a separate 9,600 Hz output gate.

The runner first executes **740 real-PROM PC129 visits** for each step and
checks the phase, selected Am27S31 byte and Y7/B5 recurrence at every visit.
It then projects the checked recurrence far enough to sample 640 gate events.
At the assumed oscillator and sample rates there are `375/k` PC129 visits
per output sample. It screens every distinct integer phase offset and every
fractional gate alignment:

```text
PC129 visit sampled at output event j = offset + floor((j × 375 + δ) / k)
```

The phase-index period is 16 visits for step 48 and 32 for step 56. Thus the
screen covers 160 and 320 distinct alignments, respectively. Every alignment
for a given step and divisor has the same strongest B5 DFT bin:

| k | PC129 visits per sample | Step 48: B5 peak | Step 56: B5 peak |
| ---: | ---: | ---: | ---: |
| 1 | 375 | 3,000 Hz | 300 Hz |
| 2 | 187.5 | 1,500 Hz | 150 Hz |
| 3 | 125 | 4,200 Hz | 3,300 Hz |
| 4 | 93.75 | 4,050 Hz | 4,725 Hz |

None peaks at the intended 1,800/2,100 Hz. The largest target-bin variance
fraction over all fast-clock alignments is 0.065 for step 48 and 0.028 for
step 56, versus 0.661 and 0.486 when each PC129 visit is declared a 9,600 Hz
sample. Making **every** PC129 visit a 9,600 Hz sample from the 14.4 MHz
oscillator would instead require 375 oscillator periods per microinstruction
in this four-word loop. No such divider has been traced.

The [machine report](results/photo-127-clock-alias.json) retains the executed
trace digests, recurrence check, all alignment counts, peak distributions,
target-bin fractions and source hashes. The long sample series are mathematical
projections of an executed recurrence, not full emulated runs at those lengths.
This excludes **this direct gated-PC129 timing family**, not a slower clock,
a different effective phase step, a held-data circuit or another output
path. The earlier photo-B5 peak remains a conditional signal clue, not a
verified modem carrier or a reason to wait for a physical trace.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_clock_alias.py
```
