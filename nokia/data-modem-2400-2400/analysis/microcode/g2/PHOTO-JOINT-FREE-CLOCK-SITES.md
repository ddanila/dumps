# A free-running DAC clock does not select one ALU output site

The [site replay](photo_joint_free_clock_sites.py) runs the real PROMs twice,
once per controller call/answer selector, through the same uninterrupted A1
tone, A2 capture-off, A3 `FF` fill and A4 data fixture as the
[joined transmitter test](PHOTO-JOINT-TONE-TRAINING-DATA.md). Each run executes
1,248,256 microinstructions and checks 312,054 `129` ROM reads and ALU
results. This time a hypothetical **free-running** latch clock captures the
Am2901 Y bus every 1,500 microinstructions, or 9,600 times/s if one
microinstruction occupies one period of the photographed 14.4 MHz oscillator.
Four fixed phases sample Y at `127`, `128`, `129` or `12A`. No PROM-output
edge or PC129 qualifier is assumed. The [result](results/photo-joint-free-clock-sites.json)
stores full-code sample hashes, first codes, tone fits and data scores.

| Y site at latch edge | A1 2,100 Hz fit R², selected DAC bus | A3→A4 errors, all 12 buses |
| --- | ---: | ---: |
| `127` | 0.610480 | 0/62 |
| `128` | 0.610480 | 0/62 |
| `129` | 0.335990 | 0/62 |
| `12A` | 0.608836 | 0/62 |

Both controller selectors give these figures. `127` and `128` capture
identical Y streams in the executed trace. The `129` selected-bus digest
exactly matches the earlier joined replay; all four site streams are now
captured from the full real-PROM trace. The different R² values show that the
site changes the candidate byte waveform, even though the tone peak and
symbol decisions survive.

This weakens the earlier attempt to identify `129` as *the* output latch
site from a tone peak and external decoding alone. The phase accumulator at
`127`/`128` can supply those same signatures without selecting the ROM-shaped
`129` result. A stronger output test must distinguish the predicted analog
sample shape, pulse shaping and physical latch/DAC route; a reference decoder
that accepts multiple byte waveforms cannot make that choice.

The photograph shows a 74LS273 near the DAC08 and a 74LS373 on its other
side, but neither their data path nor clock is traced. A free-running 9,600
Hz clock and fixed phase are still assumptions, as is the one-period
microinstruction timing. This result supplies a simpler **runnable** clock
alternative to a PC129-qualified 375-visit gate; it does not establish which
one the board uses or satisfy C2. Next compare the four actual byte streams
with a pulse-shaped reference and photo-compatible 74LS373/74LS273 capture
rules, then continue independent receive/echo tests.
