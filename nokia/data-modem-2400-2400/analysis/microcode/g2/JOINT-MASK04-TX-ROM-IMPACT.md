# Selected PC129 ROM data changes internal arithmetic, not candidate Y7

The [full-stream bank ablation](JOINT-MASK04-TX-ROM-BANK-ABLATION.md)
found identical sampled candidate transmitter bytes after switching the
Am27S31 bank at `129`. This [short differential trace](joint_mask04_tx_rom_impact.py)
locates the effect. Both scenarios execute the same first 4,096 cycles
of the assumed A1 tone-mode `127–12A` loop with the same `88` input;
only the `129` bank changes. The upper bank at `12E` is held fixed.

| Compared field | Different cycles / 4,096 | Where |
| --- | ---: | --- |
| Selected `129` ROM byte | 1,014 / 1,014 reads | `129` |
| ALU `f` | 1,172 | `129`: 951; `12A`: 221 |
| Register writes | 1,393 | `129`: 951; `12A`: 221; `128`: 221 |
| ALU Y byte | 221 | `12A` only |
| **ALU Y7** | **0** | All four loop words |
| Q, current/next PC | **0** | All four loop words |

The first difference is at cycle 42, PC `129`: the upper-bank read
returns `04` from `17A`, while the lower-bank read returns `16` from
`07A`. Both are selected by the ALU. Its `f` result and R0 write change
(`66` versus `56`), but Y is `76` in both runs. Some later `12A` Y
**lower bits** do differ; the full modeled states are equal again after
4,096 cycles. The 12 sampled Y bytes at the first three free-clock
instants across phases `127`, `128`, `129` and `12A` are identical.
The [full-stream replay](JOINT-MASK04-TX-ROM-BANK-ABLATION.md) extends
sample identity to all 832 phase-`129` candidate samples per selector.

This establishes a narrower mechanism than “the ROM is ignored.” The
selected operand participates in arithmetic and temporary state, but
the tested bank change does not alter Y7 or the proposed 9,600 Hz
output samples. It does not rule out effects from individual ROM bytes,
other operating modes, different latch phases, or another output node.
C2 remains open. The next experiment should trace the physical latch
source or perturb a specific `129` byte while inspecting a later
mode/output path.

The [machine report](results/joint-mask04-tx-rom-impact.json) contains
the first differing instruction, per-field and per-PC counts, final
states, trace hashes and source hashes. Reproduce from the microcode
directory with `python3 g2/joint_mask04_tx_rom_impact.py`.
