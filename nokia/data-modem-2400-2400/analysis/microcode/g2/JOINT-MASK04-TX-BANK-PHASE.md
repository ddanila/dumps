# A `12A` latch phase exposes selected ROM-bank data in the candidate DAC stream

The [full controller-fed bank-phase replay](joint_mask04_tx_bank_phase.py)
extends the [PC129 bank ablation](JOINT-MASK04-TX-ROM-BANK-ABLATION.md)
to the next executed Y site. It runs each call (`40`) and answer (`60`)
A1–A4 stream for **1,248,256 real-PROM instructions** with the selected
Am27S31 A8 bank at `129` set first to upper and then lower. The other
mapping, controller input, `12E` bank and modeled clock are fixed. Each
run reaches `129` and `12A` 312,054 times; none reaches `12E`.

| Selector | Site | Changed raw Y visits | Fixed 375-visit clock phases seeing a change | Changed 832 sample bytes at phase 0 |
| --- | --- | ---: | ---: | ---: |
| Call `40` | `129` | 0 | 0/375 | 0 |
| Call `40` | `12A` | 75,012 | **375/375** | **198** |
| Answer `60` | `129` | 0 | 0/375 | 0 |
| Answer `60` | `12A` | 75,018 | **375/375** | **202** |

Every changed raw `12A` Y byte differs **only in bit 0**. All six
photo-compatible DAC-bus survivors assign source Y0 to DAC code bit 4,
so each changed candidate DAC sample differs by 16 counts. This is why
the earlier `129` sample stream was bank-insensitive even though its
selected ROM operand was active: a latch capturing `12A` can see a
later, bank-dependent byte that a `129` latch misses. The short 4,096-word
tone-window check happened to sample unchanged visits at phase 0; the
complete controller-fed streams show the difference later.

At the phase-0 `12A` latch candidate, both bank choices preserve a
**2,100 Hz** late-A1 peak and **0/62** externally filtered A3/A4 data
errors on each of the six DAC bus hypotheses, for both selectors. A
seven-visit offset still sees bank-dependent bytes but gives one call
and one or two answer errors, depending on the bus/bank. The same shift
also worsens the `129` candidate. Thus carrier and data scores alone
do not distinguish the two bank choices, while a precise DAC-code or
analog waveform observation could. The phase-0 result supplies a
photo-compatible ROM-sensitive output hypothesis for C2, contingent on
the latch and line route.

The modeled free-running latch takes one byte every 375 four-word loop
visits; calling that 9,600 samples/s assumes one 14.4 MHz oscillator
period per microinstruction. The Y-to-74LS273 data route, latch clock,
DAC08 bus, analog shaping, physical A8 source and line connector remain
untraced. The six buses share the Y0 weight here, but the photo has not
identified the full bus. This is a modeled causal relation, not a C2
physical output pass. Next constrain a `12A`-timed clock/data route or
an output-node waveform against the predicted 16-count bank-dependent
sample changes; keep C2 and G2 active.

The [machine report](results/joint-mask04-tx-bank-phase.json) records all
375 phase-difference counts per selector/site, paired full-trace hashes,
selected sample hashes, tone peaks and six-bus data scores. Reproduce
from this directory with `python3 g2/joint_mask04_tx_bank_phase.py`.
