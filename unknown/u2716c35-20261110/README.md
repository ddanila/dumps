# Unidentified U2716C35 — 2026-11-10

A loose U2716C35 supplied as a control during the RF2 address-alias investigation.
The owner thinks it **may be from Robotron**, either a keyboard or another ROM;
this provenance is not confirmed.

Two read-only acquisitions produced identical 2048-byte images:

- Existing RD2716.COM, conservative timing: execution 1765036003.
- Separate assembly address shifter in RF2EXP.COM: execution 837206548.

Both exited zero. Programming VPP remained off, no programming pulses were sent,
and both rails were switched off at completion. SHA256SUMS and manifest.json
identify the image and reader binaries.

## Contents and address-line check

There are recognizable Z80 instruction sequences (DD/FD prefixes, CB bit
operations and ED instructions), with several code references in the 6xxx/7xxx
ranges. This is preliminary inspection, not board identification or execution
validation; no readable product banner was found. This is not the diagnostic
pattern previously written to the RF2.

Every address bit A0–A10 distinguishes some contents. A6 pairs differ in 1508
of 2048 comparisons; A9 pairs differ in 2032 of 2048 comparisons (pairs counted
in both directions). The previous RF2 candidates' A6/A9 mirrors are absent.
This strengthens a chip-dependent input/decode or electrical-loading explanation,
rather than a permanently stuck programmer address output. It does not measure
the RF2's actual input voltage.

## Comparison before preservation

No exact or embedded match was found among **134 distinct reference images**
(161 comparisons including duplicate sources/archive copies). The full 2048
bytes were searched at every possible offset in larger references, so padding
or inclusion in a larger ROM does not hide an exact match.

References include S600, S642 JCUKEN and S642 QWERTY/ЯВЕРТЫ keyboard firmware;
PC1715 system/font/FDC ROMs; K8915 firmware; and the broader
[DDR firmware collection](https://oldpc.su/articles/de_roms/DE_ROMs.html).
Other download sources were [MCbx PC1715](https://oldcomputer.info/8bit/robo1715/index.htm)
and [Tiffe K8915](https://www.tiffe.de/robotron/K8915/Eprominhalte/).
The local MAME source/hash catalog also contains no matching SHA1.

The S600 and S642 reference images differ in 1616–1618 bytes; this is not an
identical copy of those known keyboard ROMs. `comparison.json` records sources,
reference hashes, results and the one broken collection link (`files/.rom`).
`comparison.tsv` provides aligned-byte difference counts. Public reference
binaries remain outside this repository. The originating system is still
unknown, and these checks do not establish uniqueness across the entire Internet.

Full serial traces remain in local DOSRAVI sessions
u2716c35-20261110-unknown-read1 and u2716c35-20261110-unknown-read2.
The DOS machine's 1980 timestamps are not the acquisition date.
