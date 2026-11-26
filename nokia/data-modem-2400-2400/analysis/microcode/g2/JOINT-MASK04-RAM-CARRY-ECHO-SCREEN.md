# The sustained previous-carry RAM route amplifies the tested echo proxy

The [functional replay](joint_mask04_ram_carry_echo_screen.py) uses the
same own-transmit, independent remote, mixed and zero inputs as the
[corrected low-nibble screen](JOINT-MASK04-EXTERNAL-RAM-ECHO-SCREEN.md).
The own-echo source comes from the saved real-PROM call transmitter, delayed
three PCM samples and halved; the independent remote signal is a different
reference DPSK stream at quarter gain. Each input has 128 training samples
and a common 64-sample zero tail. Eight cases run **288,047 real-PROM words**
each with the [surviving previous-carry TEST hypothesis](JOINT-MASK04-RAM-CONDITION-RESCUE.md).

The assumed 256×8 RAM latches `3F9` Y's high nibble, writes at `3EC`,
advances one address per held ADC sample, and returns a byte from three
samples behind into `3FA` D high nibble. A write-only control uses the
same RAM address and freeze schedule without returning it. All eight
cases complete **9,000 ADC visits**, with no `3ED→3EE` exits. Each route
writes 24,000 times during the first 128 samples and freezes afterward.
The high-return route performs 9,000 reads and changes `3FA` Y in 141
visits of the common tail versus the same-input write-only control.

The table compares `3FA` **unsigned byte differences**, a diagnostic of
the proposed output site, not a measured analog residual:

| Route | Early mixed vs remote | Late mixed vs remote | Late differing visits | Common-tail mixed vs remote |
| --- | ---: | ---: | ---: | ---: |
| Write only | 0.251 | 0.439 | 658 | 0 |
| High return | 13.556 | **17.796** | **1,312** | 2.256 |

The own-echo-versus-zero late difference also grows from zero to 5.973;
remote-versus-zero grows from 0.313 to 8.803. This is neither selective
own-echo attenuation nor a falling late response at the tested `3FA`
site. The common-tail difference shows stored input still affects the
executed code after writes freeze, but it is not evidence of frozen
canceller weights. In this address schedule, only the first three tail
samples revisit written addresses, which explains the 141-visit
same-input tail effect.
The [word-level arithmetic audit](JOINT-MASK04-RAM-CARRY-ARITHMETIC.md)
checks all 24,000 training `3FA` calculations and finds R10=`10` at
every operand read. Its Y high nibble is the returned D high nibble plus
two modulo sixteen; the low bit is the current carry input. R10 changes
elsewhere in the loop, but supplies no varying estimate at this site.

The TEST mux, RAM bus/counter/write/read pins, ADC and analog output
remain explicit photo-compatible assumptions. The prior-overflow
high-return exit cannot be generalized to previous-carry; conversely,
this sustained previous-carry route does **not** pass C4. Next test a
plausible signed or mode-qualified return, or find a different output
site, with the same own/remote/mixed and write-only controls. Require
selective late residual reduction and a commanded freeze before calling
the routine an echo canceller. G2 remains active.

The [machine report](results/joint-mask04-ram-carry-echo-screen.json)
records all eight trace/input/RAM hashes, difference counts and freeze
windows. Reproduce from this directory with
`python3 g2/joint_mask04_ram_carry_echo_screen.py`.
