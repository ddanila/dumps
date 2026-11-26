# A simple external RAM feedback route does not sustain the receive loop

The [bus screen](JOINT-UPPER-RAM-BUS-SCREEN.md) found no direct 8-bit RAM
address on Am2901 Y and no single-word active-low PROM write bit. This
[counterfactual run](joint_upper_ram_feedback_screen.py) adds one explicit
external route to the existing joint mask-`08` PROM execution, without
changing the shared emulator. The [DSC 3557 photograph](../../../photos/PXL_20261123_114811760.jpg)
shows four MCM93422 256×4 RAMs beside a 74LS163 counter and 74LS157 mux.
Their placement motivates the route, but does not establish its nets.

The candidate uses a 256-address counter incremented at `3EA`, an 8-bit
RAM bank initially filled with `01`, a latch of `3FA` or `3F9` Y, and a
write at `3EC` driven by an assumed inversion or decode of the U18 D2/D4
pulse. It returns one RAM nibble to D at `3EB`, keeping D0 high. The
8-bit bank would require two of the photographed 4-bit RAMs; the visible
single 4-bit counter cannot alone generate the eight address bits. The
address extension, data pins, latch, write gate and return route are all
untraced. D0 forcing preserves the loop's observed `01` mode input and is
also an explicit assumption.

The same real PROM mapping and initial state run for 768 intended ADC
visits. The input is 256 deterministic codes in `80…176`, followed by
512 visits at `127`. Read-only, write-only and no-feedback controls each
complete all 768 visits with the same modeled Am2901 trace digest. The
write-only route writes all 256 RAM addresses, so the candidate memory is
actually exercised.

| Candidate readback and latch | `3F8` visits | Loop exit | Effect |
| --- | ---: | --- | --- |
| High nibble, `3FA` Y | 258 | `3ED→3EE` once | First changed return byte is `21` at address 2; modeled execution leaves the loop. |
| Low nibble, `3FA` Y | 768 | None | RAM changes, but the modeled Am2901 trace is identical to no feedback. |
| High nibble, `3F9` Y | 331 | `3ED→3EE` once | Different latch timing still leaves the loop. |

For the first route, the first two revisited RAM addresses return `01`;
the third returns `21` at `3EB`. The next `3ED` branches to `3EE` and
enters another program region. Thus a high-nibble RAM return can affect
control flow, but this simple counter/write/read timing is not a sustained
receive or echo-training path. The low-nibble route's identical trace
shows that storing data alone is not evidence of DSP feedback under this
mapping.

The result rejects only these declared wiring and timing fixtures. A
different address source, gated train/freeze write, read timing, data
format or controller mode route could behave differently. Next, test a
photo-compatible write gate during training followed by freeze, and
compare residual and RAM history against own-echo, remote-only and
zero-input controls. C4 and G2 remain open and active; no continuity
measurement is needed to run that test.

The [machine report](results/joint-upper-ram-feedback-screen.json) records
trace digests, exit counts, RAM hashes and source/photo hashes. Reproduce
from the microcode directory with
`python3 g2/joint_upper_ram_feedback_screen.py`.
