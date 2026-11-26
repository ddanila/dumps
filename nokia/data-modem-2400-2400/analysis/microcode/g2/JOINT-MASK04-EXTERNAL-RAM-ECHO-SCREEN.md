# Corrected sample-paced external-RAM echo screen

This [four-row real-PROM replay](joint_mask04_external_ram_echo_screen.py)
compares zero input, an independent remote DPSK waveform, the candidate
own-transmit waveform delayed three PCM samples and halved, and their mixture.
Each has 128 training samples and a common 64-sample zero tail. The modeled
RAM is 256×8, initially `01`; one hypothesized route latches `3F9` Y's low
nibble, writes at `3EC`, and returns an address three samples behind into
`3FA` D's low nibble. Each of 20 cases executes **288,047 real-PROM words**
and completes **9,000 ADC visits** without leaving the four-row loop.

**Timing correction.** The first version of this screen treated one `3EA`
or `3EC` occurrence as one ADC visit, but the selected receive loop executes
each address **four times per ADC visit**. Its claimed 128-sample write gate
actually froze after 32 samples, and all 192 supplied address ticks had
already fired by about sample 48. Its late and tail scores therefore did
not test the described sample-paced RAM. The script and
[machine report](results/joint-mask04-external-ram-echo-screen.json) now use
four `3EC` writes per ADC visit (**24,000 training writes**) and multiply
each sample-clock tick position by four. The results below replace the
earlier interpretation.

The `3FA`-Y low-nibble latch stores only the initial `01` in all four
inputs and its return has no effect. The `3F9`-Y low-nibble latch stores
128/81/93/97 noninitial addresses after zero/own/remote/mixed training.
With its three-sample-lag return at `3FA`, the PROM trace changes and the
common zero tail differs from the same-input write-only control at `3FA`
on 141/94/141/94 visits, respectively. `3F8` and `3F9` do not change in
that tail. Returning the same byte at the earlier `3EB` site leaves every
trace identical to its no-feedback control. Thus the executed loop can
respond to delayed, stored input through **this assumed `3FA` return**;
the effect is site-specific.

The table shows mean absolute unsigned `Y3FA` code differences between
remote-plus-echo and remote-only inputs. This is an output-code proxy, not
a measured analog line residual.

| Route | First 32 training samples | Last 32 training samples | Common zero tail |
| --- | ---: | ---: | ---: |
| `3F9` latch, write/freeze only | 0.251 | 0.439 | 0 |
| `3F9` latch, return −3 samples at `3FA` | 4.992 | 6.065 | 0.313 |

The remote-minus-zero response in the last training window also grows from
0.313 to 3.693 under feedback. This tested route does **not** selectively
attenuate the own-echo component; its late code-space difference increases.
The tail difference shows memory readback but not useful adaptation. A
[one-sample freeze-and-read test](JOINT-MASK04-RAM-PULSE-FREEZE.md) isolates
the causal delay: one changed RAM address produces a matching delayed
`3FA` change at three and sixteen samples, while write-only and no-write
controls have no delayed change.

The RAM pins, address counter/mux, low-nibble return, D0 forcing, write
gate, train/freeze signal and ADC/DAC paths remain untraced hypotheses.
Neither a stored history nor a larger `Y3FA` difference is an echo
cancelled analog residual. C4 stays open and G2 active. Next test a
mode-qualified or alternate return and output site with the same
own/remote/mixed controls; a candidate C4 pass needs selective residual
reduction and generalization, not only RAM activity. Reproduce with
`python3 g2/joint_mask04_external_ram_echo_screen.py` from the microcode
directory.
