# Puritan Bennett 7200 MEGACPU EPROMs

Owner reports nine EPROM positions numbered 0 through 8, with chip 7
missing. Only chip 0 has been read so far; 1–6 and 8 remain pending.
Board reference photo: `/home/ddanila/Downloads/133870106.jpg`.
Chip 0's socket designation and full sticker text are not yet confirmed.
Other visible ROMs carry `26300-85-V`; that label is not assigned to chip 0
without a readable photograph or independent evidence.

## Chip 0 acquisition

Read twice on 2026-11-14 with T48 firmware 00.1.03, minipro 0.7.4:

```sh
minipro -p M27512@DIP28 -x -r OUTPUT.bin
```

Both operations exited zero and produced identical 65536-byte captures.
ID probing was disabled; no programming or erase command was issued.
The profile specifies 5 V read/verify voltage, not an independently measured
chip-rail value. Minipro reports incomplete T48 support and firmware older
than expected. Original logs and metadata are in `evidence/`; both raw
reads remain in the session path recorded in `manifest.json`.

The chip is provisionally treated as a standard-pinout 28-pin 27-series
EPROM, per the owner's description. Exact physical type and capacity are
unconfirmed. CRC32 of the complete unmodified capture is `bc8a5f28`.

## Initial content inspection

The lower 32 KiB is entirely `CC`. The upper 32 KiB contains code-like bytes,
diagnostic text and more CC-filled regions. The image does not repeat at
2, 4, 8, 16 or 32 KiB boundaries. This does not establish 64 KiB physical
capacity: a smaller device may have different control/supply pin functions
under this provisional profile. No padding has been stripped.

Readable text includes `Q1 PROM ERROR`, `Q2 PROM ERROR`, `MULTIBUS RAM ERROR`,
`ADC     OUT OF TOLER`, `BUV IS ON`, `LOW  AC  POWER`, and `SETUP ERROR`.
At offset `fff0`, bytes `ea 00 00 c0 ff` decode as the 16-bit x86 far jump
`JMP FFC0:0000`. If mapped at the top of the first MiB, that targets offset
`fc00` in this image, where the byte stream begins with plausible I/O-port
initialization instructions. Together these observations strongly suggest
boot/power-on-self-test firmware, unlike the Q1–Q3 sensor data ROMs.
No execution or full disassembly has been performed in this acquisition.

The manufacturer's [parts list](https://doczz.net/doc/2483138/puritan-bennett-7200)
identifies the MegaCPU as 80188-based, consistent with the x86 reset sequence.
Public searches by capture SHA-256, CRC32 and system name found no matching
downloadable dump. Internet uniqueness is not established.
