# Two exact anti-symmetric byte regions temper the phase-step interpretation

The [ROM scan](rom_antisymmetric_regions.py) reads the original 512-byte
Am27S31 dump as signed bytes and searches the `30–7F` region for exact
anti-symmetric contiguous windows of at least eight bytes. It finds two
maximal windows:

| Addresses | Signed bytes |
| --- | --- |
| `5A–69` | `−1, 0, 6, −16, 25, −33, 40, −46, 46, −40, 33, −25, 16, −6, 0, 1` |
| `72–7B` | `6, −22, 46, −68, 81, −81, 68, −46, 22, −6` |

Both read identically to the negative of their reverse and sum to zero.
This is exact structure in the dumped data; it is **not yet a decoded FIR,
Hilbert filter or pulse shape**. If treated as consecutive signed taps at
the *hypothetical* 9,600 samples/s rate, both have zero DC gain and a
15 Hz-grid maximum at 4,800 Hz, far above their gains at 1,800/2,100 Hz.
Their actual read order and clock may differ.

The earlier [fast-step candidate screen](PHOTO-127-FAST-STEP-CANDIDATES.md)
noted `F0` at `5D` and `10` at `66`. These are **−16 and +16 at opposite
positions of the same 16-byte window**. Their co-occurrence is therefore
poor evidence that the ROM stores two independent D127 phase-step
parameters. The modular fast-clock solutions remain mathematically valid;
the claim that this ROM region supplies those steps has no supporting
dataflow.

As an execution check, a q3 lower-bank, held-D127=`01` run reads each byte
of both windows once at PC129. A paired upper-bank run has identical
post-PC128 RAM/Q/flag/stack checkpoints. The lower-bank path sweeps almost
the whole ROM, so these reads do not identify an intended coefficient
consumer, and the selected bytes do not survive that loop under the tested
mapping. The [machine report](results/rom-antisymmetric-regions.json) saves
the windows, conditional frequency responses, paired trace digests and
source hashes.

The next useful program-level test is to find a controller- or sample-driven
address sequence that selects these windows **and** retains their values
for a multiply, filter state or output. A structural table match alone
does not satisfy G2's transmit or receive checks.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/rom_antisymmetric_regions.py
```
