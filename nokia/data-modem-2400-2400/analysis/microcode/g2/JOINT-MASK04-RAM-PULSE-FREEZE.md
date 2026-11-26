# A stored ADC pulse returns after the chosen RAM delay

The [matched-tail impulse test](JOINT-MASK04-RECEIVE-IMPULSE-MEMORY.md)
found that the current four-row PROM fixture has no captured state
difference after a one-sample ADC pulse ends. This
[external-RAM replay](joint_mask04_ram_pulse_freeze.py) tests one declared
way for the photographed MCM93422 memory to supply that missing history.
It does not assume the pin connections are established.

Eight real-PROM runs use the same 64-sample reference waveform and change
only ADC sample 25 from `51` to `B1`. The input streams rejoin at sample
26. Each run executes **96,047 microinstructions**, completes **3,000 ADC
visits**, and retains the four-row loop. The hypothetical 256×8 RAM begins
at `01`, latches `3F9` Y's low nibble, writes at `3EC` through sample 25,
then freezes. Its address increments once per held ADC sample. A selected
read returns the byte into `3FA` D's low nibble with D0 forced high.

The timing counts matter: `3EA` and `3EC` each execute **four times per ADC
visit**. This replay therefore schedules one address tick at four times
each ADC sample-start visit and freezes after **4,876 writes**, which is
four times the 1,219 ADC visits through sample 25. With this schedule,
the pulse changes exactly one frozen RAM byte, address 26, from `01` to
`0F`.

| Route | Frozen RAM difference | `3FA` differences after pulse | First delayed `3FA` codes, baseline→pulse |
| --- | --- | --- | --- |
| Write/freeze, no readback | address 26 | 0 | — |
| Readback, −3 samples | address 26 | 47 visits at sample 28 | `20→2E` |
| Readback, −16 samples | address 26 | 47 visits at sample 41 | `20→2E` |
| Readback −16, writes disabled | none | 0 | — |

The delayed windows begin at ADC visits 1,313 and 1,922, respectively.
Neither readback route differs between pulse and baseline in the frozen
tail **before** its expected read window. Both differ for just the 47
visits that read the pulse address, then rejoin. `3F8` and `3F9` have no
delayed difference. The no-write and no-feedback controls exclude a
direct persistent effect of the ADC pulse in this fixture: the delayed
`3FA` change is carried by the modeled RAM byte and its assumed return.

This is conditional evidence that a photo-compatible external memory
route can make executed PROM output depend on a past ADC sample. It is
not evidence that this exact RAM net exists, that `3FA` is an analog
residual, or that the microprogram cancels echo or decides received
bits. The corrected [own/remote/mixed screen](JOINT-MASK04-EXTERNAL-RAM-ECHO-SCREEN.md)
shows that this same return **increases** the late mixed-versus-remote
`3FA` difference, so C4 remains open. C3 and G2 remain open and active.
The next useful test should change the mode or return/output site and
require selective residual reduction or a downstream receive decision,
with write-only and no-write controls retained.

Run `python3 g2/joint_mask04_ram_pulse_freeze.py` from the microcode
directory. The [machine report](results/joint-mask04-ram-pulse-freeze.json)
records case hashes, changed RAM bytes and first/last output differences
for each pulse and delayed window.
