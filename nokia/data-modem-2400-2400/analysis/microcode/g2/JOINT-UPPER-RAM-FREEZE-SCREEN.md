# A frozen RAM route can change the receive loop, but has no demonstrated echo function

The [first feedback screen](JOINT-UPPER-RAM-FEEDBACK-SCREEN.md) tested a
free-running counter and RAM. This [follow-up](joint_upper_ram_freeze_screen.py)
lets the assumed `3EC` write gate close after 256 writes, leaving one
RAM byte at each counter address. Two independent 256-visit ADC prefixes
in `80…176` are followed by the same 128-visit code-`127` tail. All runs
use the real PROMs and the same joint mask-`08` mapping and initial state.
The write-enabled, no-readback run is a trained-RAM control. Neither the
gate nor its source is a traced board connection.

The frozen RAMs retain different prefix histories: 61 of 256 bytes differ
between the two no-feedback runs. With low-nibble `3EB` readback, 217
bytes differ, yet both modeled Am2901 traces exactly match their own
no-feedback controls. A free-running low-nibble `3EB` route also leaves
both traces unchanged. Storing distinct bytes alone therefore does not
show that this input lane consumes them.

| RAM return route | Prefix `3557` | Prefix `3558` | Tail behavior versus same-prefix control |
| --- | --- | --- | --- |
| High nibble at `3EB` | Exits after 258 ADC visits | Completes 384 visits | In the surviving run, 1,018 of 1,024 tail trace rows differ and final internal state differs. |
| Low nibble at `3EB` | Completes 384 visits | Completes 384 visits | Neither trace changes. |
| High nibble at `3FA` | Exits after 4 ADC visits | Exits after 4 ADC visits | No sustained tail. |
| Low nibble at `3FA` | Completes 384 visits | Completes 384 visits | 122 and 114 of 1,024 tail rows differ; the first prefix leaves R13 at `30` instead of `20`, while the second ends at the control state. |

This exposes a real conditional difference in executed PROM behavior:
the `3FA` low-nibble read route can carry a frozen training history into
the common tail without leaving the receive loop. It does **not**
establish that this is the photographed RAM's wiring or an echo-canceller
tap. The two prefixes are synthetic, one ADC code is presented per
receive-loop visit, and no line residual is measured. With the assumed
counter increment on every `3EA`, the 256-address memory spans only
256 loop visits, not 256 ADC sample periods under the prior 188/187-visit
sample hold. A sample-paced counter is the next meaningful clock variant.

Next, clock the candidate address once per held ADC sample, train on
controller-derived own echo and an independent remote signal, freeze the
writes at the training boundary, then compare the executed output and
residual against zero-input and no-feedback controls. Keep the clock,
readback, write gate, DAC/ADC routes and C4 conditional. No missing
continuity trace blocks that runnable test.

The [machine report](results/joint-upper-ram-freeze-screen.json) records
per-route trace and RAM hashes, exit counts, first changed reads, and
tail-row differences. Run `python3 g2/joint_upper_ram_freeze_screen.py`
from the microcode directory to reproduce it.
