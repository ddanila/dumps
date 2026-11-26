# A high-nibble RAM return at `3FA` breaks the sustained receive loop

The [replay](joint_mask04_ram_high_return_exit.py) tests another explicit
external-RAM hypothesis suggested by the four photographed MCM93422 256×4
parts on DSC 3557. Two such parts could provide a 256×8 bank. The model
latches the **high** nibble of executed `3F9` or `3FA` Y, writes at each
`3EC` during the first 26 held ADC samples, advances its address once per
sample, and returns a value from three samples behind into the **high**
nibble of `3FA` D with D0 forced high. The counter extension, latch,
write gate and return pins remain assumed.

Five 96,047-word real-PROM runs use the same legal 64-sample waveform as
the [low-nibble freeze test](JOINT-MASK04-RAM-PULSE-FREEZE.md). The controls
separate writes from readback; an additional run changes ADC sample 25
from `51` to `B1`.

| Route | Selected ADC visits | `3ED→3EE` loop exits | First noninitial RAM read | Exit cycle |
| --- | ---: | ---: | --- | ---: |
| `3F9` latch, write only | 3,000 | 0 | none | — |
| Read only, RAM initialized to `01` | 3,000 | 0 | none | — |
| `3F9` latch, high return at `3FA` | 939 | 1 | cycle 4,577: `21` from address 1 | 30,082 |
| `3FA` latch, high return at `3FA` | 423 | 1 | cycle 4,577: `21` from address 1 | 13,570 |
| `3F9` latch, high return, sample-25 pulse | 939 | 1 | same as unpulsed | 30,082 |

The `3F9` high-return baseline and pulse have identical full trace
digests: both leave the receive loop before the offered pulse begins at
ADC visit 1,172. Write-only and read-only traces match the original
unmodified receiver baseline. Thus the exit requires **stored data to
return through this D lane**, not RAM writes alone or an unchanged `01`
read. The first changed read precedes the exit, but the thousands of
intervening words mean this is a sustained control-flow effect, not a
claim that one `21` byte directly trips the branch.

The [post-exit trace extension](joint_mask04_ram_high_return_exit.py)
follows the program beyond `3EE`. Both variants run the same 53-word
transition through `18D`, `270` and other setup words, then alternate
at `1E9/1EA` without returning to the ADC loop. For the `3F9` latch,
**65,911 of 65,964** post-exit words are at those two addresses; for
the `3FA` latch, **82,423 of 82,476** are. The last sixteen PCs in
each trace are eight repetitions of `1EA,1E9`. This rules out the exit
being a productive alternate receiver within the tested run and
strengthens the route-specific rejection. A different condition source
could release that loop; the condition wiring is still an assumption.

This rejects the two tested high-nibble `3FA` return fixtures as models
of a sustained receiver or useful echo-training loop. It does not reject
the photographed RAMs, a different read timing, write enable, mode or
output site. The already tested low-nibble return sustains the loop but
increases the own-echo code-space proxy; neither result is a measured
echo residual. Next test a mode-qualified or differently timed return
with own/remote/mixed and no-write controls, and require selective late
attenuation plus a freeze response before passing C4. G2 remains active.

The [machine report](results/joint-mask04-ram-high-return-exit.json)
records input and trace hashes, read/write counts, first changed reads
the executed branch rows and the complete post-exit PC histogram.
Reproduce from this directory with
`python3 g2/joint_mask04_ram_high_return_exit.py`.
