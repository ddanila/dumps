# Tandberg TDV-2200S-family firmware on TMM27128AD-20

A 16 KiB **8085 terminal firmware** image containing low-level services and the
beginning of a terminal application. Long exact code sequences and the hardware
I/O map connect it to the Tandberg TDV-2200S family. It implements an 80-column,
25-row display, serial communications, keyboard/printer interfaces, nonvolatile
configuration, and 16 programmable PUSH-key slots. The physical terminal model,
board position and firmware revision are not established.

## Identification and contents

The [analysis](analysis/README.md) includes an annotated recursive disassembly,
140 service jump-table entries, four control/key dispatch tables, memory and
I/O maps, startup/self-test logic, public-ROM comparison, and execution probes.
The original bytes pass 80,909 isolated execution cases, including exhaustive
screen-coordinate validation, queue wraparound, and a deliberately failed RAM
test. This is not a complete terminal boot: application code and resources at
4000h–57FFh are absent from this chip.

The image is **not blank**: 16,310 bytes differ from FFh. Its SHA-256 is
`739c871b383c216428ee833d2758b7590ab4e589b76a065dece91e532cfb1849`.

| File | Purpose |
|---|---|
| [tmm27128ad-20.bin](tmm27128ad-20.bin) | Unmodified physical-chip capture, 16,384 bytes |
| [manifest.json](manifest.json) | Identity, acquisition and checksums |
| [analysis/README.md](analysis/README.md) | Findings, evidence, limits and reproduction commands |
| [analysis/disassembly.asm](analysis/disassembly.asm) | Addressed 8085 code and unclassified data |
| [analysis/probe-results.json](analysis/probe-results.json) | Isolated original-code execution results |

## Comparison before preservation

No exact or embedded match was found against 19 public TDV-2200/2200S ROM/PROM
images or 97 existing local `.bin` files. Word-byte-swapped public references
were checked too. Public references stay outside this repository.

The closest inspected reference is `965090-24 -1-.27128.u93`, published in the
[Supermagnum/Tandberg archive](https://github.com/Supermagnum/Tandberg/tree/main/TDV-2200/ROM-Files).
It has 2,613 equal bytes at identical offsets; a relocation-tolerant sequence
comparison finds 7,941 equal bytes in ordered matching blocks. The first 65
bytes match exactly, as do numerous long routines. This supports family
identification, not a claim that the two images are the same revision.
[Comparison records](analysis/comparison.json) pin the source URLs and hashes;
the checked collection does not establish uniqueness across the entire Internet.

## Acquisition

- Date: 2026-11-26. Owner-reported marking: **TMM27128AD-20**.
- T48, serial `6MNNWV7B0LLRDYCAA5PF5744`, firmware `00.1.03`.
- MiniPro 0.7.4, compatible read profile `27128A@DIP28`; `-x` skips electronic
  identification. Toshiba's [datasheet](https://deramp.com/downloads/mfe_archive/050-Component%20Specifications/Toshiba/Memory/Toshiba%20TMM27128A.pdf)
  specifies pin compatibility with i27128A.
- Contact test passed. Two full reads succeeded and matched byte for byte.
- Read command: `minipro -p '27128A@DIP28' -x -r readN.bin`.
- Observed supply: 4.98 V in the contact check. Reader logs retain their own
  reported values and the incomplete-support/outdated-firmware warnings.
- No programming, erasing or firmware update was performed.
- Local session: `rom-programmers/sessions/tmm27128ad-20-blank-check-20261126-222318`.
  Both original [read1.log](evidence/read1.log) and [read2.log](evidence/read2.log)
  are preserved unchanged. The second identical binary remains in that session.
