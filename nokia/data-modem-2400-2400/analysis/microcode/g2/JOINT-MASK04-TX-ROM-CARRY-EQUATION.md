# The selected `129` ROM operand reaches `12A` Y0 through high-slice carry

The [split-slice arithmetic replay](joint_mask04_tx_rom_carry_equation.py)
checks every reached `129→12A` pair in four 4,096-word real-PROM runs:
upper and lower selected Am27S31 A8 banks, each under held A1 tone
input `88` and a data-prefix control (dibit `11` encoded as D127=`90`
for four visits, then baseline `B0`). Each run reaches 1,014 pairs.
Both bank choices take the same PC path within each input fixture.

At `129`, the checked low instruction is `C9` and the high instruction
is `8D`. With A=R1, B=R0 and the selected ROM byte as D, the executed
split-slice equations are (`~` means four-bit complement):

```text
low129  = (~R1lo + R0lo + carry_in) mod 16
high129 = (~ROMhi + R1hi + carry_from_low129) mod 16
carry129 = carry out of high129
```

Both slice results write R0; Y's high nibble still exposes R1hi.
At the immediately following `12A`, checked instructions `C1/85`
produce:

```text
low12A = (R1lo + R0lo_from_129 + carry129) mod 16
Y12A   = R1hi : low12A
```

The audit reconstructs pre-word R0/R1 from every register write and
checks F, Y, carry and the written R0 byte at **all 8,112 audited
words**. It also checks that `129` carry becomes the `12A` carry input.

| Input fixture | ROM bytes different / 1,014 | R0 bytes after `129` different | `129` carries different | `12A` Y bytes different |
| --- | ---: | ---: | ---: | ---: |
| Held tone `88` | 1,014 | 951 | **221** | **221** |
| Data `11` pulse then `B0` | 1,014 | 1,014 | **254** | **254** |

Across both fixtures, R1 and the low R0 nibble entering `12A` are
identical between banks. Every `12A` Y difference coincides exactly
with a `129` high-carry difference; each Y XOR mask is `01`. This
explains the earlier [short differential trace](JOINT-MASK04-TX-ROM-IMPACT.md)
and the bit-0-only result in the
[full controller-fed bank screen](JOINT-MASK04-TX-BANK-PHASE.md). The
ROM-selected high-slice calculation is active, even though a proposed
DAC sample at `129` or Y7 alone does not expose it.

The selected A8 bank, D127 inputs, split-slice wiring, latch capture
phase and DAC/line route are still explicit hypotheses. The short
data-prefix fixture is an arithmetic control, not a complete
controller-fed modem call. A bank-dependent `12A` byte is conditional
digital C2 evidence, not a measured analog output.

The [machine report](results/joint-mask04-tx-rom-carry-equation.json)
contains all equation checks, paired-bank difference counts, trace
digests and source hashes. Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_tx_rom_carry_equation.py
```
