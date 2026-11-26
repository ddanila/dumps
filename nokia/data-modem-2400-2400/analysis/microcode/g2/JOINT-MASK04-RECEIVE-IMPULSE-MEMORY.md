# A one-sample receive perturbation does not persist in the current four-row fixture

The [sampled-byte identity audit](JOINT-MASK04-FULL-BUS-ADC-ROW-IDENTITY.md)
showed that direct `3F8` and selected `3ED` captures expose quantized ADC
samples. This experiment asks whether the **downstream executed state**
retains a change after the ADC input becomes identical again.

Six real-PROM receive runs use the same joint mask-`04` mapping,
four-row dispatch, previous-overflow TEST assumption and `D3EB=01`.
Each run supplies 64 held ADC samples over 3,000 ADC visits and executes
96,047 microinstructions. The first triplet holds ADC `7F`, changing
sample 24 alone to `BF` (high-nibble pulse) or `70` (low-nibble control).
The second triplet uses a varying 8-symbol reference waveform; its ADC
sample 25 is `51`, changed alone to `B1` or `5E`. In both triplets the
baseline and altered streams have the same prefix and the same complete
tail after the changed sample. All six PC-sequence digests match.

| Input fixture | High-nibble change | Changed captured channels during the pulse | Differences after the 47-visit pulse | Low-nibble change |
| --- | --- | --- | ---: | --- |
| Constant `7F` | `7F→BF` | `3F8`/`3F9`/`3FA` Y, Q, R1 | 0 | `7F→70`: captured state and trace digest identical |
| Varying reference | `51→B1` | same, plus R12 | 0 | `51→5E`: captured state and trace digest identical |

Each changed channel differs on exactly the 47 ADC visits that hold the
altered sample, and rejoins on the **first visit after** it. The captured
post-`3FA` `3ED` Y, other registers and program path do not differ in
these fixtures. The low-nibble controls yield the same executor trace digest
as their baselines, consistent with the checked `3F8` high-nibble
equation. These are controlled impulse responses, not a mere comparison
of unrelated line streams.

Under this explicit mode and input route, the active ROM and Q/RAM
arithmetic responds to the current ADC high nibble but shows **no
cross-sample memory** for either single-sample perturbation. That is a
substantial limit on interpreting this four-row path as a complete
demodulator or echo canceller. It does not reject an unmodeled external
RAM return, mode-qualified training path, different TEST/dispatch lane,
or an output not captured here. No received bit reaches USART-01 in this
test; C3/C4 and G2 remain open and active.

Next, run a photo-compatible external RAM or mode-control hypothesis with
write-enabled training and frozen readback, using the same matched-prefix
and common-tail controls. Require a persistent or selectively attenuated
downstream state before treating a candidate path as receive/echo work.

Run `python3 g2/joint_mask04_receive_impulse_memory.py` from the
microcode directory. The [machine report](results/joint-mask04-receive-impulse-memory.json)
records every channel's first/last difference, pulse boundary, trace and
PC hashes, and source hashes.
