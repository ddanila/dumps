# Landis & Gyr UNIGYR PRU_AC — six-chip program card

These six external memories contain **Motorola 68HC11 firmware and application
configuration for a Landis & Gyr UNIGYR controller**, very likely a PAA1-family
program card used in a PRU1 process unit. The firmware build string is
`PRU_AC  4-NOV-1993 14:47:13`. PAA1.2A/PAA1.3A are plausible candidates;
the exact PCB, MCU suffix and controller model remain unconfirmed.

The [deep analysis](analysis/README.md) records the architecture survey,
reset/vector and peripheral evidence, thirteen code banks, serial diagnostics,
configuration text and reproducible scripts. The firmware's original checksum
passes (`c9`) across 229352 bytes of chips 5 and 6. This is an eight-bit
checksum with documented exclusions, not a complete verification of all six
memories. Chips 3–4 contain Estonian and Finnish building-control labels.
**Chip 2 repeats a 128-byte page; its full-address validity is unresolved.**

The owner numbered six chips from one PCB: chips 1–4 are 28C64 (8 KiB each),
and chips 5–6 are M27C1001 (128 KiB each). All six are included unchanged.
Chip 5 has two identical physical reads; the others have one each. Acquisition
spanned 2026-09-24 through just after midnight on 2026-09-25 in Europe/Tallinn;
the directory retains its start date. Other package markings and sticker text
have not been established. See the analysis for manufacturer attribution sources.

## Acquisition and verification

Both chip-5 reads used the Willem PCB5.0E, Pocket8086 LPT378, DIP634, Normal
routing and full 32-pin placement. Programming VPP remained off.

| Method | Timing profile | Read time, including chunk I/O |
|---|---|---:|
| Portable C address shifter, RD010V1.COM | fast | 1803.065 s |
| 8086 assembly address shifter, RD010V2.COM /FASTADDR | conservative | 715.935 s |

All 131072 bytes match: **2.52× speedup**, CRC16-CCITT `401c`,
CRC32 `b134c0a6`. Both runs exited successfully and reported safe power
shutdown. The 64 KiB halves differ; the final 8 KiB is all zero. The final 16 KiB
is not entirely padding: it includes a small, unresolved data area. Agreement
establishes repeatability on this setup, not independent proof of every
address or the device's operation in its original board.

The first run's binary download timed out after the read completed. A
standalone GET with a 20-second timeout recovered the existing file and
verified its remote CRC32; its CRC16 also matches the reader. The original
`session.json` retains the transfer error. See `evidence/capture-analysis.json`.
The second run downloaded successfully. DOS timestamps are not real dates;
the host acquisition date above is authoritative. WILLEM.LOG is cumulative.
Full serial logs, duplicate images and reader binaries/source snapshots
remain in the local DOSRAVI sessions listed in `manifest.json`.

## Chip 1

Single 8 KiB 28C64 capture using `R28C64 /PROFILE:conservative`, completed
in 112.310 seconds. DIP12B, Normal routing, two empty ZIF rows at the lever
end; VCC 5 V and programming VPP off. Safe shutdown reported.
CRC16-CCITT `4198` matches the reader; CRC32 `8ab497de` matches the
remote download checksum. Nonblank, with 162 distinct byte values and no
clear identifying ASCII strings. Not repeat-read verified. Evidence is in
`evidence/chip01-read1/`.

## Chip 2 — repeated-page capture, validity unresolved

Single 8 KiB 28C64 capture with the same DIP12B read setup as chip 1,
completed in 112.255 seconds. Safe shutdown reported. CRC16-CCITT `e332`
and downloaded CRC32 `3ee0f6fd` were verified. It differs from chip 1 at
6499 byte positions and contains no identifying ASCII strings.

**The same 128-byte block repeats 64 times.** This may be stored data or
address aliasing; a successful transfer and checksum do not distinguish
them. Preserve as an unverified capture, not confirmed full-address contents.
No second physical read was performed. Evidence: `evidence/chip02-read1/`.

## Chip 3

Single 8 KiB 28C64 capture using the same DIP12B conservative read setup,
completed in 112.310 seconds with safe shutdown. CRC16-CCITT `54d2`
matches the reader; downloaded CRC32 `c18f8919` was verified. It differs
from chips 1 and 2, has 64 distinct 128-byte pages, and has no whole-image
repetition at any power-of-two period smaller than its size.

Contains readable Estonian and Finnish control labels: `AJAPROGRAMM`,
`AUTOMAATIKA`, `Reklaamvalgustus`, `Sisevalgustus`,
`Mittevastavuse alarm`, `SJ.SM4:PULSSI_LASKURI`, and
`Skaalaus:1 pulssi=`. These suggest application/configuration text for
lighting, alarms and pulse counters; the exact installation remains unknown.
Not repeat-read verified. Evidence and extracted ASCII fragments are in
`evidence/chip03-read1/`; non-ASCII characters are omitted by ASCII extraction.

## Chip 4

Single 8 KiB 28C64 capture using the same DIP12B conservative read setup,
completed in 112.310 seconds with safe shutdown. CRC16-CCITT `a24f`
matches the reader; downloaded CRC32 `d0fe2145` was verified. It differs
from chips 1–3, contains 41 distinct 128-byte pages, and has no whole-image
repetition at any power-of-two period smaller than its size.

More Estonian and Finnish control labels, including `0=Kell, 1=Ajaprogramm`,
`HK Valgustuse andur`, `SM.SM1:PULSSI_LASKURI`, and
`Automaattisen resetin arvo`. These are consistent with application/configuration
text related to lighting, alarms and pulse counters. Not repeat-read verified.
Evidence and ASCII fragments: `evidence/chip04-read1/`.

## Chip 6

Single 128 KiB read using the same verified assembly reader and conservative
timing, completed in 716.320 seconds (11m56s), with safe shutdown.
Host CRC16-CCITT `10d4` matches the DOS reader; downloaded CRC32 `a0a09b07`
was checked against DOSRAVI. It differs from chip 5 at 113288 byte positions,
and its two 64 KiB halves differ. No meaningful identifying ASCII strings
were found. It has not been repeat-read verified; attribution to the same
board comes from the owner. Evidence is in `evidence/chip06-read1/`.

## Public-dump comparison

No matching public ROM was located by exact hash, build-string and firmware
searches, or in the local MAME sources/hash lists. This is not proof of
Internet uniqueness. Queries and attribution sources are recorded in
`evidence/known-rom-search.md`.
