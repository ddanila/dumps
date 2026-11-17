# MB005 LC-2516 ROM set — acquisition in progress

Source: [MB005 Turbo XT mainboard](https://github.com/ddanila/vintage-computer-inventory/blob/main/items/MB005-turbo-xt/README.md),
revision V1.02, marking `NO:T 790704677`, with Acer chipset per owner.

## LO/EVEN acquisition — 2026-11-17

28-pin EPROM labelled **LC-2516**, **LO/EVEN**. The owner reports **27256**
on the PCB silkscreen beneath it; the chip's full manufacturer/type markings
remain unknown. Two T48 reads using `M27256@DIP28` with ID probing skipped
(`-x`) match byte for byte. No programming was performed.

- Size: 32,768 bytes; no repeated 2, 4, 8 or 16 KiB blocks across the image.
- SHA-256: `07e68544193883c513a89f71814fa52e04007a54bd33d58f47a8083b53e3cd36`
- CRC32: `df89a5a2`
- Byte sum modulo 256: zero; this alone does not validate a full BIOS.

Text fragments appear to contain alternating characters of BIOS messages,
consistent with the even-byte lane of a paired ROM set. The image remains
unaltered. **The companion ROM is still required** to reconstruct and identify
the complete firmware; no combined BIOS or emulator validation is claimed.

Original commands, reader hash and logs are in `evidence/lo-even/`. The raw
repeat reads also remain in the local session recorded in `manifest.json`.

## Public comparison

Compared against 780 files of 32, 64 or 128 KiB in the local
[86Box ROM collection](https://github.com/86Box/roms) at revision
`52264223de5f3df1b51861481ee116eed47eca3e`, checking whole-file equality and
equality to each candidate's even and odd byte lanes. No exact match found.
This limited comparison does not establish uniqueness. Label searches did
not identify the firmware; identification awaits the companion image.
