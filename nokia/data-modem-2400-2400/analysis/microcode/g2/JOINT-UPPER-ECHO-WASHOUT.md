# Echo stimulation leaves no lasting state in the fixed receive fixture

The earlier [own-echo screen](JOINT-UPPER-ECHO-OUTPUT-SCREEN.md) found
no rapid selective attenuation during 128 ADC samples. A useful next
question is whether those samples at least train a retained state.
This [washout replay](joint_upper_echo_washout.py) runs the joint
upper-source mask-`08` mapping for four real-PROM traces of 288,047
microinstructions each: all-zero input, independent remote DPSK input,
and own-transmit echo from each controller selector. The three active
inputs occupy the first 128 samples; all four traces then receive the
**same 64 zero samples**. The own-echo prefixes come from the
hash-checked controller-derived A4 candidate DAC streams, delayed by
three samples and scaled by one half.

At every `3FA` receive-loop visit, the replay records Y at `3F8–3FA`,
Q and all 16 modeled Am2901 RAM bytes. Each trace has 36,000 selected
ADC visits, with the prior 188/187-visit sample hold and complementary
ADC code. The late training state differs from the zero control, so
the inputs are active rather than silently ignored:

| Prefix before common zero tail | Different observed bytes on last training visit | Tail visits with different RAM | Last different tail visit | Full final emulator state equals zero control? |
| --- | ---: | ---: | ---: | --- |
| Independent remote | 7 | 2 | 1 | Yes |
| Own echo, call `40` | 7 | 3 | 2 | Yes |
| Own echo, answer `60` | 4 | 3 | 2 | Yes |

All 20 observed bytes match the zero control from tail visit 3 onward
in both echo cases, far before the first complete zero sample. This
rules out a long-lived **internal Q/RAM tap state under this exact fixed
mapping, ADC schedule and mode**. A longer repetition of the same
fixture is unlikely to uncover a retained echo estimate at these
modeled sites. It does not rule out cancellation using the photographed
external MCM93422 RAMs, a different input/mode route, or an output latch
that the fixture does not model. No train/freeze command or line
residual is demonstrated, so C4 remains open.

The [machine report](results/joint-upper-echo-washout.json) contains
the three paired trace/ADC hashes, per-channel tail differences and
source hashes. Reproduce from the microcode directory with
`python3 g2/joint_upper_echo_washout.py`.
