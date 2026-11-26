# PC129 ROM-bank choice does not drive the candidate transmit samples

The joint mask-`04` transmitter configures the Am27S31 upper bank at
both `129` and `12E`. This [causal replay](joint_mask04_tx_rom_bank_ablation.py)
keeps the real four-PROM mapping, controller-derived call/answer input,
free-running sample clock, six photo-compatible DAC bus orders and
assumed analog filter fixed. It independently changes the A8 bank at
`129` or `12E`, then executes each complete A1–A4 stream for
1,248,256 microinstructions.

| Selector | Bank changed | Address visits | Full trace | Captured 832-byte Y stream | Tone / A3–A4 |
| --- | --- | ---: | --- | --- | --- |
| `40` call | `129` | 312,054 | Changed | **Identical SHA-256** | Same 2,100 Hz peak; 0/62 errors on six buses |
| `60` answer | `129` | 312,054 | Changed | **Identical SHA-256** | Same 2,100 Hz peak; 0/62 errors on six buses |
| Either | `12E` | **0** | Unchanged | Identical | Unchanged |

The counterfactual runs complete the same candidate waveform and change
their full trace digests, while their captured Y sample hashes exactly
match the upper-bank baselines. Thus the particular **PC129 bank choice is
not causal for the sampled transmit waveform in this fixture**. The
2,100 Hz peak and decoded dibits cannot be cited as evidence that the
upper-bank `129` bytes synthesize the carrier. Switching `12E` is a
**null control**, because the sustained `127–12A` loop never reaches it;
its unchanged trace is not evidence about `12E`'s function in another
mode. This does not show that the Am27S31 as a whole is irrelevant:
the choice of address, timing and other microcode operations can still
affect the output. The DAC clock, bus and analog line route remain assumed.

The result narrows the C2 mechanism before further physical-route work.
Next inspect where the `129` operand first affects internal state and
test a specific changing byte there. A separate A1 fixture that actually
reaches `12E` is needed to test that operand. Keep C2 open and G2 active;
an untraced wire is not a blocker.

The [machine report](results/joint-mask04-tx-rom-bank-ablation.json)
contains address-visit counts, baseline/counterfactual trace and sample
hashes, six bus scores per selector, and source hashes. Reproduce from the microcode directory
with `python3 g2/joint_mask04_tx_rom_bank_ablation.py`.
