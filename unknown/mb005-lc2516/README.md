# MB005 LC-2516 / LC-2517 BIOS ROM pair

Source: [MB005 Turbo XT mainboard](https://github.com/ddanila/vintage-computer-inventory/blob/main/items/MB005-turbo-xt/README.md),
revision V1.02, marking `NO:T 790704677`, with Acer chipset per owner.

## Acquisition — 2026-11-17

Both chips are 28-pin 27-series EPROMs with **27256** on the PCB silkscreen
beneath their sockets; full chip manufacturer/type markings remain unknown.
Each was read twice with the T48 using `M27256@DIP28`, skipping electronic ID
probing (`-x`). Both pairs of 32 KiB reads match exactly. No programming was
performed. Original logs, commands and analysis are under `evidence/`.

| Label | Raw file | SHA-256 |
| --- | --- | --- |
| LC-2516, LO/EVEN | `lc2516-lo-even-27256.bin` | `07e68544193883c513a89f71814fa52e04007a54bd33d58f47a8083b53e3cd36` |
| LC-2517, HI/ODD | `lc2517-hi-odd-27256.bin` | `672407c58f6dfae9a0865823d5716385fc0890ae1f25bdf638ec2ef3006b5f2a` |

## Reconstruction and identification

`mb005-xt-plus-201b-interleaved.bin` is 65,536 bytes. At each chip offset i,
LO/EVEN supplies combined byte 2*i and HI/ODD supplies byte 2*i+1. No byte
correction or padding was applied. The original chip images remain preserved.

The reconstructed image contains:

- `8086 XT-plus BIOS Version 2.01B`
- `ACER0010XTplus10 1.0201/09/89`
- `***INVESTRONICA S.A.`
- Date `05/20/88` in the reset-vector area (distinct from the Acer identifier).
- Setup messages for date/time, floppy drives and fixed-disk formatting.

At offset FFF0h, `EA 5B E0 00 F0` decodes as a far jump to F000:E05B.
Both chip images and the combined image have byte sums of zero modulo 256.
Readable text, the reset vector and these sums support the reconstruction;
**no emulator or physical motherboard boot test has been performed**. The BIOS
banner identifies an 8086 XT-plus firmware; the physical CPU marking is not
yet recorded.

Combined SHA-256: `6f23f71380ea7169abf3c6f25e0ddfd40dc7babe407ab32bf059eddc958250a4`

## Public comparison

No match was found in 780 local 86Box ROM files of 32, 64 or 128 KiB at
[collection](https://github.com/86Box/roms) revision
`52264223de5f3df1b51861481ee116eed47eca3e`. The LO/EVEN search included even/odd
lanes; the HI/ODD search compared whole files and searched for the full combined
image within candidates.

A [2016 Sannata forum thread](https://phantom.sannata.org/viewtopic.php?t=21825&start=44)
reports a BIOS64.ROM with the same Acer, Investronica and version strings.
Attachment retrieval is blocked by the site's user-verification page, so an
exact binary comparison remains outstanding. This acquisition is **not claimed
to be unique**. The reported matching strings alone do not establish byte equality.
